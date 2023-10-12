from ..models import PublishedLessons, Roles, DraftLessons
import db
from helpers.types import InsertResults
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import Union
from datetime import datetime


def _insert_new_publish_lesson(
    lesson: PublishedLessons,
    **kwargs,
) -> InsertResults[PublishedLessons]:

    try:
        res = db.PUBLISHED_LESSONS_COLLECTION.insert_one(
            lesson.dict(to_db=True), **kwargs
        )
    except DuplicateKeyError:
        return InsertResults(exists=True)
    except Exception as e:
        return InsertResults(failure=True)

    lesson.id = res.inserted_id

    return InsertResults(success=True, value=lesson)
