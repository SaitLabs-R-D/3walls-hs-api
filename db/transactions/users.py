from helpers.types import RequestWithFullUser
from db import updates, queries
from typing import Union
from bson import ObjectId
from services.gcp import GCP_MANAGER
from .common import Transaction, TransactionResult, ClientSession


def fully_delete_user(user_id: Union[str, ObjectId], request: RequestWithFullUser):
    def the_tran(
        session: ClientSession,
        user_id: Union[str, ObjectId],
        request: RequestWithFullUser,
    ):
        draft_id: str = None
        # deleting user
        delete_user_res = updates.delete_user_by_id(user_id, request, session=session)

        if delete_user_res.failure:
            return TransactionResult(
                success=False,
                message="Failed to delete user",
            )

        user = delete_user_res.value

        # trying to get a user to pass lessons to
        pass_lessons_user = None
        if user.account:

            user_res = queries.get_account_manager_user(user.account, session=session)
            update_account_user_count_res = updates.update_account_current_users_count(
                user.account, -1, session=session
            )
            if update_account_user_count_res.failure:
                return TransactionResult(
                    success=False,
                    message="Failed to update account users count",
                )

            if user_res.failure:
                if user_res.not_found:
                    pass
                else:
                    return TransactionResult(
                        success=False,
                        message="Failed to get account manager user",
                    )
            else:
                pass_lessons_user = user_res.value

        if pass_lessons_user is None:

            user_res = queries.get_system_admin_user(session=session)
            if user_res.failure:
                return TransactionResult(
                    success=False,
                    message="Failed to get admin user",
                )

            pass_lessons_user = user_res.value

        # if there is no user to pass lessons to, we can't delete the user
        if pass_lessons_user is None or pass_lessons_user.id == user.id:
            return TransactionResult(
                success=False,
                message="No user to pass lessons to",
            )

        # deleting the current user draft lessons
        user_draft_lessons_res = updates.delete_draft_lesson_by_creator_id(
            user.id, session=session
        )

        if user_draft_lessons_res.failure:
            if not user_draft_lessons_res.not_found:
                return TransactionResult(
                    success=False,
                    message="Failed to delete user draft lessons",
                )
        else:
            # if the user has a draft lesson, we need to delete the draft lesson from GCP
            # so we save the draft id to delete it later
            draft_id = str(user_draft_lessons_res.value.id)

        # changing the creator of the user published and archived lessons to the user to pass lessons to
        if updates.change_many_published_lessons_creator(
            user.id, pass_lessons_user.id, session=session
        ).failure:
            return TransactionResult(
                success=False,
                message="Failed to change published lessons creator",
            )

        if updates.change_many_archived_lessons_creator(
            user.id, pass_lessons_user.id, session=session
        ).failure:

            return TransactionResult(
                success=False,
                message="Failed to change archived lessons creator",
            )

        if (
            updates.change_many_editors_of_published_lessons(
                user.id, pass_lessons_user.id, session=session
            )
        ).failure:
            return TransactionResult(
                success=False,
                message="Failed to change editors of published lessons",
            )

        if (
            updates.change_many_editors_of_archived_lessons(
                user.id, pass_lessons_user.id, session=session
            )
        ).failure:
            return TransactionResult(
                success=False,
                message="Failed to change editors of archived lessons",
            )

        if updates.change_many_archived_by_of_archived_lessons(
            user.id, pass_lessons_user.id, session=session
        ).failure:
            return TransactionResult(
                success=False,
                message="Failed to change archived by of archived lessons",
            )

        try:
            if draft_id is not None:
                GCP_MANAGER.delete_lesson(draft_id)
        except Exception as e:
            return TransactionResult(
                success=False,
                message=f"Failed to delete draft lesson from GCP error: {e}",
            )

        return TransactionResult(success=True)

    transaction = Transaction(func=the_tran, args=[user_id, request], kwargs={})

    transaction.start()
