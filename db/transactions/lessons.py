from helpers.types import RequestWithFullUser
from db.models import (
    Actions,
    Resources,
    ArchiveLessons,
    PublishedLessons,
    DraftLessons,
    ScreensTypes,
    Users,
    Accounts,
    LessonEdit,
    LessonPart,
    LessonScreen,
)
from typing import Union
from bson import ObjectId
from services.gcp import GCP_MANAGER
from .common import Transaction, TransactionResult, ClientSession
import db
from helpers.secuirty import permissions
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from google.cloud.exceptions import NotFound
from db.inserts.lessons import _insert_new_publish_lesson


def archive_published_lesson(
    request: RequestWithFullUser,
    lesson_id: Union[str, ObjectId],
):
    def the_tran(
        session: ClientSession,
        request: RequestWithFullUser,
        lesson_id: Union[str, ObjectId],
    ):

        user_id = ObjectId(request.state.user.id)

        default_filters = permissions.build_filters(
            request,
            Resources.PUBLISHED_LESSONS,
            Actions.DELETE,
        )

        if default_filters is None:
            return TransactionResult(
                success=False,
                message="User doesn't have permissions to delete lessons",
            )

        filters = {
            db.PublishedLessons.Fields.id: ObjectId(lesson_id),
            **default_filters,
        }

        try:
            lesson = db.PUBLISHED_LESSONS_COLLECTION.find_one_and_delete(
                filters, session=session
            )
        except:
            return TransactionResult(success=False, message="Failed to delete lesson")

        if not lesson:
            return TransactionResult(success=False, message="Lesson not found")

        lesson = ArchiveLessons(**lesson, archive_by=user_id)

        try:
            db.ARCHIVE_LESSONS_COLLECTION.insert_one(
                lesson.dict(to_db=True), session=session
            )
        except:
            return TransactionResult(success=False, message="Failed to archive lesson")

        return TransactionResult(success=True)

    transaction = Transaction(func=the_tran, args=[request, lesson_id], kwargs={})

    transaction.start()

    return transaction.result


def duplicate_published_lesson(
    request: RequestWithFullUser,
    lesson_to_dup: PublishedLessons,
):
    def the_tran(
        session: ClientSession,
        request: RequestWithFullUser,
        lesson_to_dup: PublishedLessons,
    ):

        new_lesson = DraftLessons(
            creator=request.state.user.id,
            **lesson_to_dup.dict(
                exclude={
                    PublishedLessons.Fields.id,
                    PublishedLessons.Fields.creator,
                    PublishedLessons.Fields.created_at,
                    PublishedLessons.Fields.updated_at,
                    PublishedLessons.Fields.mid_edit,
                    PublishedLessons.Fields.edit_data,
                }
            ),
        )

        try:
            res = db.DRAFT_LESSONS_COLLECTION.insert_one(
                new_lesson.dict(to_db=True, exclude={"id"}), session=session
            )
        except DuplicateKeyError:
            print("User already has a draft lesson")
            return TransactionResult(
                success=False,
                message="User already has a draft lesson",
            )
        except Exception as e:
            print("Failed to save lesson into draft")
            print(e)
            return TransactionResult(
                success=False, message="Failed to save lesson into draft"
            )

        new_lesson.id = res.inserted_id
        print(new_lesson.id)
        lesson_to_dup_id = str(lesson_to_dup.id)
        new_lesson_id = str(new_lesson.id)

        url_update = {}

        # update the urls of the screens to point to the new lesson id
        for part in new_lesson.parts:
            for screen in part.screens:
                if screen.type_ in [ScreensTypes.VIDEO, ScreensTypes.IMAGE]:
                    screen.url = screen.url.replace(lesson_to_dup_id, new_lesson_id, 1)

        url_update[DraftLessons.Fields.parts] = [
            part.dict() for part in new_lesson.parts
        ]

        if isinstance(new_lesson.thumbnail, str):
            new_lesson.thumbnail = new_lesson.thumbnail.replace(
                lesson_to_dup_id, new_lesson_id, 1
            )

            url_update[DraftLessons.Fields.thumbnail] = new_lesson.thumbnail

        if isinstance(new_lesson.description_file, str):
            new_lesson.description_file = new_lesson.description_file.replace(
                lesson_to_dup_id, new_lesson_id
            )

            url_update[
                DraftLessons.Fields.description_file
            ] = new_lesson.description_file

        if url_update:
            try:
                res = db.DRAFT_LESSONS_COLLECTION.update_one(
                    {DraftLessons.Fields.id: ObjectId(new_lesson.id)},
                    {"$set": url_update},
                    session=session,
                )
            except Exception as e:
                print("Failed to update lesson urls")
                print(e)
                return TransactionResult(
                    success=False, message="Failed to update lesson urls"
                )

            if not res.modified_count:
                print("Failed to update lesson urls")
                print(res.modified_count)
                return TransactionResult(
                    success=False, message="Failed to update lesson urls"
                )

        try:
            GCP_MANAGER.duplicate_lesson(lesson_to_dup_id, new_lesson_id)
        except Exception as e:
            print("Failed to duplicate lesson in GCP")
            print(e)
            return TransactionResult(
                success=False, message="Failed to duplicate lesson"
            )

        return TransactionResult(success=True, message="Lesson duplicated successfully")

    transaction = Transaction(func=the_tran, args=[request, lesson_to_dup], kwargs={})

    transaction.start()

    return transaction.result


def restore_archived_lesson(
    lesson_to_restore: ArchiveLessons,
):
    def the_tran(
        session: ClientSession,
        lesson_to_restore: ArchiveLessons,
    ):

        lesson = PublishedLessons(
            **lesson_to_restore.dict(
                exclude={
                    ArchiveLessons.Fields.archive_at,
                    ArchiveLessons.Fields.archive_by,
                }
            )
        )

        lesson.set_updated_at()

        try:
            db.PUBLISHED_LESSONS_COLLECTION.insert_one(
                lesson.dict(to_db=True), session=session
            )
        except DuplicateKeyError:
            return TransactionResult(
                success=False,
                message="Lesson already published",
            )
        except:
            return TransactionResult(
                success=False, message="Failed to save lesson into published"
            )

        try:
            db.ARCHIVE_LESSONS_COLLECTION.delete_one(
                {ArchiveLessons.Fields.id: lesson_to_restore.id}, session=session
            )
        except:
            return TransactionResult(
                success=False, message="Failed to delete lesson from archive"
            )

        return TransactionResult(success=True)

    transaction = Transaction(func=the_tran, args=[lesson_to_restore], kwargs={})

    transaction.start()

    return transaction.result


def publish_draft_lesson(
    draft_lesson: DraftLessons,
    request: RequestWithFullUser,
):
    def the_tran(
        session: ClientSession,
        draft_lesson: DraftLessons,
        request: RequestWithFullUser,
    ):
        not_valid_res = TransactionResult(success=False, message="Lesson is not valid")

        if not draft_lesson.title:
            return not_valid_res
        elif not draft_lesson.description:
            return not_valid_res
        elif not draft_lesson.categories:
            return not_valid_res
        elif not draft_lesson.parts:
            return not_valid_res
        elif not draft_lesson.thumbnail:
            return not_valid_res

        for part in draft_lesson.parts:
            # if not part.title:
            #     raise ValueError("Part title is required")

            if part.is_panoramic():
                if not part.panoramic_url and not part.gcp_path:
                    return not_valid_res
            else:
                for screen in part.screens:
                    if not screen.url:
                        return not_valid_res

        published_lesson = PublishedLessons(**draft_lesson.dict())

        date_now = datetime.now()

        published_lesson.created_at = date_now
        published_lesson.updated_at = date_now

        insert_res = _insert_new_publish_lesson(published_lesson, session=session)

        if not insert_res.success:
            return TransactionResult(
                success=False, message="Failed to save lesson into published"
            )

        if request.state.user.account:
            user_account = request.state.user.account.id

            try:
                db.ACCOUNT_COLLECTION.update_one(
                    {Accounts.Fields.id: ObjectId(user_account)},
                    {
                        "$push": {
                            Accounts.Fields.allowed_lessons: ObjectId(
                                published_lesson.id
                            )
                        }
                    },
                    session=session,
                )
            except:
                return TransactionResult(
                    success=False, message="Failed to update account"
                )

        try:
            db.DRAFT_LESSONS_COLLECTION.delete_one(
                {DraftLessons.Fields.id: draft_lesson.id}, session=session
            )
        except:
            return TransactionResult(
                success=False, message="Failed to delete lesson from drafts"
            )

        return TransactionResult(success=True)

    transaction = Transaction(func=the_tran, args=[draft_lesson, request], kwargs={})

    transaction.start()

    return transaction.result


def delete_archived_lesson(lesson_id: Union[str, ObjectId]):
    def the_tran(session: ClientSession, lesson_id: Union[str, ObjectId]):
        lesson_id = ObjectId(lesson_id)

        try:
            lesson = db.ARCHIVE_LESSONS_COLLECTION.find_one_and_delete(
                {ArchiveLessons.Fields.id: lesson_id}, session=session
            )
        except:
            return TransactionResult(success=False, message="Failed to delete lesson")

        if not lesson:
            return TransactionResult(success=False, message="Lesson not found")

        try:
            GCP_MANAGER.delete_lesson(str(lesson_id))
        except:
            return TransactionResult(success=False, message="Failed to delete lesson")

        try:
            db.USER_COLLECTION.update_many(
                {Users.Fields.allowed_lessons: {"$in": [lesson_id]}},
                {"$pull": {Users.Fields.allowed_lessons: lesson_id}},
            )
        except:
            return TransactionResult(success=False, message="Failed to delete lesson")

        try:
            db.ACCOUNT_COLLECTION.update_many(
                {Accounts.Fields.allowed_lessons: {"$in": [lesson_id]}},
                {"$pull": {Accounts.Fields.allowed_lessons: lesson_id}},
            )
        except:
            return TransactionResult(success=False, message="Failed to delete lesson")

        return TransactionResult(success=True)

    transaction = Transaction(func=the_tran, args=[lesson_id], kwargs={})

    transaction.start()

    return transaction.result


def delete_edit_data(
    lesson_id: Union[str, ObjectId],
    request: RequestWithFullUser,
):
    def the_tran(
        session: ClientSession,
        lesson_id: Union[str, ObjectId],
        request: RequestWithFullUser,
    ):

        try:
            res = db.PUBLISHED_LESSONS_COLLECTION.update_one(
                {
                    DraftLessons.Fields.id: ObjectId(lesson_id),
                    # Only the current editor can delete the edit data
                    f"{DraftLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}": ObjectId(
                        request.state.user.id
                    ),
                },
                {
                    "$set": {
                        DraftLessons.Fields.edit_data: None,
                        DraftLessons.Fields.mid_edit: False,
                    }
                },
                session=session,
            )
        except:
            return TransactionResult(
                success=False, message="Failed to delete edit data"
            )

        if not res.modified_count:
            return TransactionResult(
                success=False, message="Failed to delete edit data"
            )
        try:
            GCP_MANAGER.delete_lesson_edit_folder(str(lesson_id))
        except NotFound:
            pass
        except:
            return TransactionResult(
                success=False, message="Failed to delete edit data"
            )

        return TransactionResult(success=True)

    transaction = Transaction(func=the_tran, args=[lesson_id, request], kwargs={})

    transaction.start()

    return transaction.result


def remove_part_from_published_lesson(
    lesson_id: Union[str, ObjectId],
    part_id: str,
    request: RequestWithFullUser,
):
    def the_tran(
        session: ClientSession,
        lesson_id: Union[str, ObjectId],
        part_id: str,
        request: RequestWithFullUser,
    ):

        try:
            res = db.PUBLISHED_LESSONS_COLLECTION.update_one(
                {
                    PublishedLessons.Fields.id: ObjectId(lesson_id),
                    PublishedLessons.Fields.mid_edit: True,
                    f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}": ObjectId(
                        request.state.user.id
                    ),
                    f"{DraftLessons.Fields.edit_data}.{LessonEdit.Fields.parts}.{LessonPart.Fields.id}": part_id,
                },
                {
                    "$pull": {
                        f"{DraftLessons.Fields.edit_data}.{LessonEdit.Fields.parts}": {
                            LessonPart.Fields.id: part_id
                        }
                    }
                },
                session=session,
            )
        except:
            return TransactionResult(
                success=False, message="Failed to remove part from lesson"
            )

        if not res.modified_count:
            return TransactionResult(
                success=False, message="Failed to remove part from lesson"
            )

        try:
            GCP_MANAGER.delete_lesson_part(str(lesson_id), part_id, edit=True)
        except NotFound:
            pass
        except:
            return TransactionResult(
                success=False, message="Failed to remove part from lesson"
            )

        return TransactionResult(success=True)

    transaction = Transaction(
        func=the_tran, args=[lesson_id, part_id, request], kwargs={}
    )

    transaction.start()

    return transaction.result


def update_screen_in_published_lesson(
    lesson_id: Union[str, ObjectId],
    part_id: str,
    screen_index: int,
    screen: LessonScreen,
):
    def the_tran(
        session: ClientSession,
        lesson_id: Union[str, ObjectId],
        part_id: str,
        screen_index: int,
        screen: LessonScreen,
    ):

        filters = {
            PublishedLessons.Fields.id: ObjectId(lesson_id),
            PublishedLessons.Fields.mid_edit: True,
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}.{LessonPart.Fields.id}": part_id,
        }

        update = {
            "$set": {
                f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}.$.{LessonPart.Fields.screens}.{screen_index}": screen.dict(),
            },
        }
        try:
            res = db.PUBLISHED_LESSONS_COLLECTION.update_one(
                filters,
                update,
                session=session,
            )
        except:
            return TransactionResult(
                success=False, message="Failed to update screen in lesson"
            )
        if not res.modified_count:
            return TransactionResult(
                success=False, message="Failed to update screen in lesson"
            )

        try:
            GCP_MANAGER.delete_part_screen_old_media(
                str(lesson_id), part_id, screen_index, screen.url, edit=True
            )
        except NotFound:
            pass
        except:
            return TransactionResult(
                success=False, message="Failed to update screen in lesson"
            )

        return TransactionResult(success=True)

    transaction = Transaction(
        func=the_tran, args=[lesson_id, part_id, screen_index, screen], kwargs={}
    )

    transaction.start()

    return transaction.result


def save_published_lesson_edits(
    # the lesson after the edits are saved
    lesson: PublishedLessons,
    blobs_to_delete: list[str],
    blobs_to_move: list[str],
):
    def the_tran(
        session: ClientSession,
        lesson: PublishedLessons,
        blobs_to_delete: list[str],
        blobs_to_move: list[str],
    ):
        try:
            res = db.PUBLISHED_LESSONS_COLLECTION.update_one(
                {
                    PublishedLessons.Fields.id: ObjectId(lesson.id),
                },
                {
                    "$set": lesson.dict(to_db=True),
                },
                session=session,
            )
        except:
            return TransactionResult(
                success=False, message="Failed to save lesson edits"
            )

        if not res.modified_count:
            return TransactionResult(
                success=False, message="Failed to save lesson edits"
            )

        try:
            # keep the order of the operations
            GCP_MANAGER.delete_list_of_lessons_files(str(lesson.id), blobs_to_delete)
            GCP_MANAGER.move_edit_files_to_publish_folder(str(lesson.id), blobs_to_move)
        except NotFound:
            pass
        except:
            return TransactionResult(
                success=False, message="Failed to save lesson edits"
            )

        return TransactionResult(success=True)

    transaction = Transaction(
        func=the_tran, args=[lesson, blobs_to_delete, blobs_to_move], kwargs={}
    )

    transaction.start()

    return transaction.result
