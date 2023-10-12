from ...models import DraftLessons, add_update_at_to_update, LessonPart, LessonScreen
import db
from helpers.types import UpdateResults
from typing import Union, Optional
from bson import ObjectId


def _update_draft_lessons(
    filter: dict, update: Union[list[dict], dict], update_at: bool = True, **kwargs
) -> UpdateResults[DraftLessons]:

    if update_at:
        update = add_update_at_to_update(update)

    try:
        res = db.DRAFT_LESSONS_COLLECTION.find_one_and_update(filter, update, **kwargs)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if res is None:
        return UpdateResults(not_found=True, failure=True)

    return UpdateResults(success=True, value=DraftLessons(**res))


def _delete_draft_lessons(filter: dict, **kwargs) -> UpdateResults[DraftLessons]:

    try:
        res = db.DRAFT_LESSONS_COLLECTION.find_one_and_delete(filter, **kwargs)
    except:
        return UpdateResults(failure=True)

    if res is None:
        return UpdateResults(not_found=True, failure=True)

    return UpdateResults(success=True, value=DraftLessons(**res))


def _delete_many_draft_lessons(filter: dict, **kwargs) -> UpdateResults[int]:

    try:
        res = db.DRAFT_LESSONS_COLLECTION.delete_many(filter, **kwargs)
    except:
        return UpdateResults(failure=True)

    if res is None:
        return UpdateResults(not_found=True, failure=True)

    return UpdateResults(success=True, value=res.deleted_count)


def get_or_create_draft_lesson(
    creator_id: Union[ObjectId, str],
):
    draft_lesson = DraftLessons(
        creator=ObjectId(creator_id),
    )

    filters = {
        DraftLessons.Fields.creator: ObjectId(creator_id),
    }

    update = {
        "$setOnInsert": draft_lesson.dict(to_db=True),
    }

    return _update_draft_lessons(
        filters, update, upsert=True, return_document=True, update_at=False
    )


def update_draft_lesson_by_id(
    lesson_id: Union[ObjectId, str],
    title: Optional[str] = None,
    description: Optional[str] = None,
    description_file: Optional[str] = None,
    categories: Optional[list[ObjectId]] = None,
    thumbnail: Optional[str] = None,
    credit: Optional[str] = None,
    # parts = "parts"
):
    filters = {
        DraftLessons.Fields.id: ObjectId(lesson_id),
    }

    update = {}

    if title is not None:
        update[DraftLessons.Fields.title_] = title

    if description is not None:
        update[DraftLessons.Fields.description] = description

    if description_file is not None:
        update[DraftLessons.Fields.description_file] = description_file

    if categories is not None:
        update[DraftLessons.Fields.categories] = categories

    if thumbnail is not None:
        update[DraftLessons.Fields.thumbnail] = thumbnail

    if credit is not None:
        update[DraftLessons.Fields.credit] = credit
    
    return _update_draft_lessons(filters, {"$set": update}, return_document=True)


def delete_draft_lesson_by_id(
    lesson_id: Union[ObjectId, str],
):
    filters = {
        DraftLessons.Fields.id: ObjectId(lesson_id),
    }

    return _delete_draft_lessons(filters)


def add_part_to_draft_lesson(
    lesson: DraftLessons,
    new_part_order: int,
    part_type: LessonPart.Types
):
    filters = {
        DraftLessons.Fields.id: ObjectId(lesson.id),
    }

    new_part = LessonPart(
        order=new_part_order,
        type=part_type,
    )

    lesson.parts.append(new_part)

    update = {
        "$set": {
            DraftLessons.Fields.parts: [part.dict() for part in lesson.parts],
        }
    }

    return _update_draft_lessons(filters, update, return_document=True)


def reorder_parts_in_draft_lesson(
    creator_id: Union[ObjectId, str],
    parts: dict[str, int],
):

    parts_ids = list(parts.keys())

    new_order = list(parts.values())

    filters = {
        DraftLessons.Fields.creator: ObjectId(creator_id),
        f"{DraftLessons.Fields.parts}": {
            "$size": len(set(parts_ids)),
            "$all": [{"$elemMatch": {LessonPart.Fields.id: {"$in": parts_ids}}}],
        },
    }

    update = [
        {
            "$set": {
                f"{DraftLessons.Fields.parts}": {
                    "$map": {
                        "input": f"${DraftLessons.Fields.parts}",
                        "in": {
                            "$mergeObjects": [
                                "$$this",
                                {
                                    LessonPart.Fields.order: {
                                        "$arrayElemAt": [
                                            new_order,
                                            {
                                                "$indexOfArray": [
                                                    parts_ids,
                                                    f"$$this.{LessonPart.Fields.id}",
                                                ]
                                            },
                                        ],
                                    },
                                },
                            ]
                        },
                    }
                }
            }
        }
    ]

    return _update_draft_lessons(filters, update, return_document=True)


def remove_part_from_draft_lesson(
    creator_id: Union[ObjectId, str],
    part_id: str,
):
    filters = {
        DraftLessons.Fields.creator: ObjectId(creator_id),
        f"{DraftLessons.Fields.parts}.{LessonPart.Fields.id}": part_id,
    }

    update = {
        "$pull": {
            DraftLessons.Fields.parts: {
                LessonPart.Fields.id: part_id,
            },
        },
    }

    return _update_draft_lessons(filters, update, return_document=True)


def update_part_screen_in_draft_lesson(
    lesson_id: Union[ObjectId, str],
    part_id: str,
    screen_index: int,
    screen: LessonScreen,
):

    filters = {
        DraftLessons.Fields.id: ObjectId(lesson_id),
        f"{DraftLessons.Fields.parts}.{LessonPart.Fields.id}": part_id,
    }

    update = {
        "$set": {
            f"{DraftLessons.Fields.parts}.$.{LessonPart.Fields.screens}.{screen_index}": screen.dict(),
        },
    }

    return _update_draft_lessons(filters, update, return_document=True)


def update_part_title_in_draft_lesson(
    creator_id: Union[ObjectId, str],
    part_id: str,
    title: str,
):
    filters = {
        DraftLessons.Fields.creator: ObjectId(creator_id),
        f"{DraftLessons.Fields.parts}.{LessonPart.Fields.id}": part_id,
    }

    update = {
        "$set": {
            f"{DraftLessons.Fields.parts}.$.{LessonPart.Fields.title_}": title,
        },
    }

    return _update_draft_lessons(filters, update, return_document=True)


def delete_draft_lesson_by_creator_id(
    creator_id: Union[ObjectId, str],
    **kwargs,
):
    filters = {
        DraftLessons.Fields.creator: ObjectId(creator_id),
    }

    return _delete_draft_lessons(filters, **kwargs)


def delete_many_draft_lessons_by_creatores_ids(
    creators_ids: list[Union[ObjectId, str]],
    **kwargs,
):

    filters = {
        DraftLessons.Fields.creator: {
            "$in": [ObjectId(creator_id) for creator_id in creators_ids]
        },
    }

    return _delete_many_draft_lessons(filters, **kwargs)


def update_draft_part_panoramic(
    lesson_id: Union[ObjectId, str],
    part_id: str,
    file_path: Optional[str] = None,
    panoramic_url: Optional[str] = None,
):
    
    filters = {
        DraftLessons.Fields.id: ObjectId(lesson_id),
        f"{DraftLessons.Fields.parts}.{LessonPart.Fields.id}": part_id,
    }

    update_set = {}

    if file_path is not None:
        if not file_path:
            file_path = None
        update_set[f"{DraftLessons.Fields.parts}.$.{LessonPart.Fields.gcp_path}"] = file_path

    if panoramic_url is not None:
        if not panoramic_url:
            panoramic_url = None
        update_set[f"{DraftLessons.Fields.parts}.$.{LessonPart.Fields.panoramic_url}"] = panoramic_url

    update = {
        "$set": update_set,
    }

    return _update_draft_lessons(filters, update, return_document=True)
