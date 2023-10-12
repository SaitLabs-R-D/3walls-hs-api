from ..models import LessonsReviews, Ratings, ReviewrInfo
import db
from helpers.types import InsertResults
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import Union


def _insert_new_lesson_review(review: LessonsReviews) -> InsertResults[LessonsReviews]:

    try:
        res = db.LESSONS_REVIEWS_COLLECTION.insert_one(review.dict(to_db=True))
    except DuplicateKeyError:
        return InsertResults(failure=True, exists=True)
    except:
        return InsertResults(failure=True)

    review.id = res.inserted_id

    return InsertResults(success=True, value=review)


def insert_new_lesson_review(
    ratings: list[Ratings],
    lesson: Union[ObjectId, str],
    user: Union[ObjectId, str],
    reviewer_name: str,
    reviewer_institution: str,
    reviewer_position: str,
    review_id: str,
    comments: str,
):

    reviewer_info = ReviewrInfo(
        name=reviewer_name,
        institution=reviewer_institution,
        position=reviewer_position,
    )

    review = LessonsReviews(
        ratings=ratings,
        lesson=ObjectId(lesson),
        user=ObjectId(user),
        reviewer=reviewer_info,
        review_id=review_id,
        comments=comments,
    )

    return _insert_new_lesson_review(review)
