from typing import Union, Any
from ..models import LessonsReviews
from bson import ObjectId
from helpers.types import QueryResults, RequestWithPaginationAndFullUser
import db
from db import aggregations
from helpers.secuirty import permissions


def get_lessons_review_for_external(
    lesson_id: Union[ObjectId, str],
) -> QueryResults[list[dict]]:

    pipeline = [
        aggregations.match_query(
            {
                LessonsReviews.Fields.lesson: ObjectId(lesson_id),
            }
        ),
        aggregations.facet(
            scores=[
                aggregations.unwind(LessonsReviews.Fields.ratings),
                aggregations.group(
                    {
                        "_id": "$ratings.name",
                        "rating": {"$avg": "$ratings.rating"},
                        "label": {"$first": "$ratings.label"},
                    }
                ),
                aggregations.sort({"_id": 1}),
                aggregations.unset("_id"),
            ],
            comments=[
                aggregations.project(
                    [LessonsReviews.Fields.reviewer],
                    comment=f"${LessonsReviews.Fields.comments}",
                )
            ],
        ),
    ]

    try:
        cursor = db.LESSONS_REVIEWS_COLLECTION.aggregate(pipeline)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    docs = next(cursor, [])

    return QueryResults(value=docs, success=True)
