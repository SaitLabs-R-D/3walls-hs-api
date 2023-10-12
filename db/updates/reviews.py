import db
from db.models import LessonsReviews
from db.queries import get_guest_role
from helpers.types import UpdateResults, RequestWithFullUser
from typing import Union, Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from helpers.secuirty import permissions


def _delete_review(filters: dict, **kwargs) -> UpdateResults[LessonsReviews]:

    try:
        review = db.LESSONS_REVIEWS_COLLECTION.find_one_and_delete(filters, **kwargs)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if review is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=LessonsReviews(**review))


def delete_review_by_id(
    review_id: Union[ObjectId, str], **kwargs
) -> UpdateResults[LessonsReviews]:

    filters = {
        LessonsReviews.Fields.id: ObjectId(review_id),
    }

    return _delete_review(filters, **kwargs)
