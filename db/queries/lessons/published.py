from ...models import (
    DraftLessons,
    Resources,
    Actions,
    PublishedLessons,
    LessonsReviews,
    RatingNames,
    LessonEdit,
    Users,
    Accounts,
)
import db
from helpers.types import (
    QueryResults,
    RequestWithPaginationAndFullUser,
    PublishedLessonPopulateOptions,
    RequestWithFullUser,
)
from typing import Union, Any, Optional
from bson import ObjectId
from typing import Optional
from helpers.secuirty import permissions
from db import aggregations

# TODO handle populate
def _get_published_lesson(
    filters: dict[str, Any],
    populate: Optional[PublishedLessonPopulateOptions] = None,
    **kwargs,
) -> QueryResults[PublishedLessons]:

    try:
        if not populate:
            lesson = db.PUBLISHED_LESSONS_COLLECTION.find_one(filters, **kwargs)
        else:
            pipeline = [
                aggregations.match_query(filters),
                aggregations.limit(1),
            ]
            pipeline.extend(populate.build_pipeline())

            lesson = db.PUBLISHED_LESSONS_COLLECTION.aggregate(pipeline, **kwargs)
            lesson = next(lesson, None)
    except:
        return QueryResults(failure=True)
    if not lesson:
        return QueryResults(not_found=True)

    return QueryResults(success=True, value=PublishedLessons(**lesson))


def validate_published_lessons_exists(
    lesson_ids: list[Union[ObjectId, str]]
) -> QueryResults[bool]:
    try:
        lessons = db.PUBLISHED_LESSONS_COLLECTION.count_documents(
            {
                DraftLessons.Fields.id: {
                    "$in": [ObjectId(lesson_id) for lesson_id in lesson_ids]
                }
            }
        )
    except:
        return QueryResults(failure=True)

    if not lessons == len(lesson_ids):
        return QueryResults(not_found=True)

    return QueryResults(success=True)


def get_published_lessons_for_external(
    request: RequestWithPaginationAndFullUser,
    category: Optional[ObjectId] = None,
) -> QueryResults[tuple[list[dict], int]]:

    default_filters = permissions.build_filters(
        request,
        Resources.PUBLISHED_LESSONS,
        Actions.READ_MANY,
    )
    pipeline = [
        aggregations.match_query(default_filters),
        aggregations.sort(
            {
                PublishedLessons.Fields.created_at: -1,
            }
        ),
    ]

    filters = {}

    if category is not None:
        filters[DraftLessons.Fields.categories] = {"$in": [ObjectId(category)]}

    if filters:
        pipeline.append(aggregations.match_query(filters))

    edit_filters = permissions.build_filters(
        request,
        Resources.PUBLISHED_LESSONS,
        Actions.UPDATE,
    )
    # if build filters returns None, it means that the user has no permissions to update any published lessons
    if edit_filters is not None:
        # if the user has permissions and filters are not empty, he can only update his own lessons
        if edit_filters:
            edit_filters = {
                "$cond": [
                    {
                        "$ne": [
                            f"${PublishedLessons.Fields.creator}._id",
                            ObjectId(request.state.user.id),
                        ]
                    },
                    False,
                    True,
                ]
            }
        # if the user has permissions and filters are empty, he can update any published lesson
        else:
            edit_filters = {
                "$cond": [
                    True,
                    True,
                    False,
                ]
            }
    else:
        edit_filters = False

    pipeline.extend(
        [
            aggregations.skip(request.state.offset),
            aggregations.limit(request.state.limit),
            aggregations.lookup(
                from_=LessonsReviews,
                local_field=PublishedLessons.Fields.id,
                foreign_field=LessonsReviews.Fields.lesson,
                as_="reviews",
                pipeline=[
                    aggregations.unwind(LessonsReviews.Fields.ratings),
                    aggregations.match_query(
                        {
                            f"{LessonsReviews.Fields.ratings}.name": RatingNames.RECOMMENDATION.value
                        }
                    ),
                    aggregations.group(
                        {
                            "_id": "$ratings.name",
                            "average": {"$avg": "$ratings.rating"},
                            "count": {"$sum": 1},
                        }
                    ),
                ],
            ),
            aggregations.unwind("reviews", True),
            aggregations.lookup(
                from_=Users,
                local_field=PublishedLessons.Fields.creator,
                foreign_field=Users.Fields.id,
                as_=PublishedLessons.Fields.creator,
                pipeline=aggregations.lookup_user_account(),
            ),
            aggregations.unwind(PublishedLessons.Fields.creator, True),
            aggregations.project(
                [
                    PublishedLessons.Fields.title_,
                    PublishedLessons.Fields.description,
                    PublishedLessons.Fields.updated_at,
                    PublishedLessons.Fields.viewed,
                    PublishedLessons.Fields.thumbnail,
                    PublishedLessons.Fields.created_at,
                    PublishedLessons.Fields.description_file,
                    PublishedLessons.Fields.categories,
                    PublishedLessons.Fields.credit,
                    "reviews",
                ],
                can_edit=edit_filters,
                creator={
                    "full_name": f"${PublishedLessons.Fields.creator}.{Users.Fields.full_name}",
                    # maybe add institution city
                    "institution": f"${PublishedLessons.Fields.creator}.{Users.Fields.account}.{Accounts.Fields.institution_name}",
                    "email": f"${PublishedLessons.Fields.creator}.{Users.Fields.email}",
                },
            ),
        ]
    )

    try:
        cursor = db.PUBLISHED_LESSONS_COLLECTION.aggregate(pipeline)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    docs = list(cursor)

    count = len(docs)

    if count < request.state.limit:
        count += request.state.offset
        return QueryResults(value=(docs, count), success=True)

    try:
        count = db.PUBLISHED_LESSONS_COLLECTION.count_documents(
            {
                **filters,
                # default filters are more important so they are last
                **default_filters,
            }
        )
    except:
        return QueryResults(failure=True)

    return QueryResults(success=True, value=(docs, count))


def get_published_lesson_by_id(
    lesson_id: Union[ObjectId, str],
    request: Optional[RequestWithPaginationAndFullUser] = None,
    populate: Optional[PublishedLessonPopulateOptions] = None,
    action: Actions = Actions.READ,
    **kwargs,
) -> QueryResults[PublishedLessons]:

    default_filters = {}

    if request is not None:
        default_filters = permissions.build_filters(
            request, Resources.PUBLISHED_LESSONS, action
        )

    if default_filters is None:
        return QueryResults(not_found=True)

    filters = {
        PublishedLessons.Fields.id: ObjectId(lesson_id),
    }

    filters.update(default_filters)

    return _get_published_lesson(filters, populate, **kwargs)


def get_published_mid_edit_lesson_for_external(
    lesson_id: Union[ObjectId, str],
    request: RequestWithFullUser,
) -> QueryResults[dict]:

    query_filters = permissions.build_filters(
        request,
        Resources.PUBLISHED_LESSONS,
        Actions.READ_UPDATE_LIMITES,
    )

    if query_filters is None:
        return QueryResults(not_found=True)

    query_filters[PublishedLessons.Fields.id] = ObjectId(lesson_id)
    query_filters[PublishedLessons.Fields.mid_edit] = True

    pipeline = [
        aggregations.match_query(query_filters),
        aggregations.limit(1),
        aggregations.add_fields(
            show_transfer_editor={
                "$cond": {
                    "if": {
                        "$eq": [
                            f"${PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}",
                            f"${PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.initial_editor}",
                        ]
                    },
                    "then": False,
                    "else": True,
                }
            },
        ),
        aggregations.unset(
            PublishedLessons.Fields.creator,
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}",
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.initial_editor}",
        ),
    ]

    try:
        cursor = db.PUBLISHED_LESSONS_COLLECTION.aggregate(pipeline)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    doc = next(cursor, None)

    if doc is None:
        return QueryResults(not_found=True)

    return QueryResults(success=True, value=doc)
