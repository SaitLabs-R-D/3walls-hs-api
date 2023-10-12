from ...models import DraftLessons
import db
from helpers.types import QueryResults
from typing import Union, Any
from bson import ObjectId


def _get_draft_lesson(filters: dict[str, Any]) -> QueryResults[DraftLessons]:
    try:
        lesson = db.DRAFT_LESSONS_COLLECTION.find_one(filters)
    except:
        return QueryResults(failure=True)

    if lesson is None:
        return QueryResults(failure=True, not_found=True)

    return QueryResults(value=DraftLessons(**lesson), success=True)


def get_draft_lesson_by_creator(creator: Union[ObjectId, str]):
    return _get_draft_lesson({DraftLessons.Fields.creator: ObjectId(creator)})


def get_draft_lessons_ids_by_creators(
    creators: list[Union[ObjectId, str]],
    **kwargs,
) -> QueryResults[list[ObjectId]]:
    try:
        ids = db.DRAFT_LESSONS_COLLECTION.distinct(
            DraftLessons.Fields.id,
            {
                DraftLessons.Fields.creator: {
                    "$in": [ObjectId(creator) for creator in creators]
                }
            },
            **kwargs,
        )
    except:
        return QueryResults(failure=True)

    return QueryResults(value=ids, success=True)


def get_draft_lesson_by_id(
    lesson_id: Union[ObjectId, str],
    **kwargs,
) -> QueryResults[DraftLessons]:
    return _get_draft_lesson({DraftLessons.Fields.id: ObjectId(lesson_id)}, **kwargs)
