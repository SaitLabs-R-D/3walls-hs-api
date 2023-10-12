from ...models import (
    Resources,
    Actions,
    ArchiveLessons,
    Users,
)
import db
from helpers.types import (
    QueryResults,
    RequestWithPaginationAndFullUser,
    RequestWithFullUser,
)
from typing import Union, Any
from bson import ObjectId
from typing import Optional
from helpers.secuirty import permissions
from db import aggregations
from datetime import datetime, timedelta


def _get_archive_lesson(
    filters: dict[str, Any], populate: None = None
) -> QueryResults[ArchiveLessons]:

    try:
        lesson = db.ARCHIVE_LESSONS_COLLECTION.find_one(filters)
    except:
        return QueryResults(failure=True)

    if not lesson:
        return QueryResults(not_found=True)

    return QueryResults(success=True, value=ArchiveLessons(**lesson))


def get_archived_lessons_for_external(
    request: RequestWithPaginationAndFullUser,
) -> QueryResults[tuple[list[dict], int]]:

    default_filters = permissions.build_filters(
        request,
        Resources.ARCHIVED_LESSONS,
        Actions.READ_MANY,
    )

    pipeline = [
        aggregations.match_query(default_filters),
        aggregations.skip(request.state.offset),
        aggregations.limit(request.state.limit),
        aggregations.lookup(
            from_=Users,
            local_field=ArchiveLessons.Fields.creator,
            foreign_field=Users.Fields.id,
            as_=ArchiveLessons.Fields.creator,
        ),
        aggregations.unwind(ArchiveLessons.Fields.creator, True),
        aggregations.project(
            [
                ArchiveLessons.Fields.archive_at,
                ArchiveLessons.Fields.title_,
            ],
            creator=f"${ArchiveLessons.Fields.creator}.{Users.Fields.full_name}",
        ),
    ]
    try:
        cursor = db.ARCHIVE_LESSONS_COLLECTION.aggregate(pipeline)
    except:
        return QueryResults(failure=True)

    docs = list(cursor)

    count = len(docs)

    if count < request.state.limit:
        count += request.state.offset
        return QueryResults(value=(docs, count), success=True)

    try:
        count = db.ARCHIVE_LESSONS_COLLECTION.count_documents(default_filters)
    except:
        return QueryResults(failure=True)

    return QueryResults(success=True, value=(docs, count))


def get_archive_lesson_by_id(
    lesson_id: Union[str, ObjectId],
    request: Optional[RequestWithFullUser] = None,
) -> QueryResults[ArchiveLessons]:

    query = {ArchiveLessons.Fields.id: ObjectId(lesson_id)}

    if request:
        default_query = permissions.build_filters(
            request,
            Resources.ARCHIVED_LESSONS,
            Actions.READ,
        )

        if default_query is None:
            return QueryResults(failure=True)

        query.update(default_query)

    return _get_archive_lesson(
        query,
    )


def get_expired_archive_lessons_ids() -> QueryResults[list[ObjectId]]:

    try:
        ids = db.ARCHIVE_LESSONS_COLLECTION.distinct(
            ArchiveLessons.Fields.id,
            {
                ArchiveLessons.Fields.archive_at: {
                    "$lt": datetime.utcnow() - timedelta(days=30)
                }
            },
        )
    except:
        return QueryResults(failure=True)

    return QueryResults(success=True, value=ids)
