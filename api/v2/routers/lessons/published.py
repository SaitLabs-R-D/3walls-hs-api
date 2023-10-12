from fastapi import APIRouter, Depends, Path, Query
from ...middleware import pagintor, check_user_permission, Actions, Resources
from helpers import fields
from helpers.types import (
    RequestWithPaginationAndFullUser,
    responses,
    RequestWithFullUser,
)
from db import queries, transactions
from services.gcp import GCP_MANAGER
from typing import Optional

router = APIRouter()


@router.get(
    "",
    dependencies=[
        Depends(pagintor),
        Depends(
            check_user_permission({Resources.PUBLISHED_LESSONS: [Actions.READ_MANY]})
        ),
    ],
)
def get_all_published_lessons(
    request: RequestWithPaginationAndFullUser,
    category: Optional[fields.ObjectIdField] = Query(None),
):

    lessons_res = queries.get_published_lessons_for_external(request, category=category)

    if lessons_res.failure:
        return responses.ApiError(message="failed to get published lessons", code=500)

    lessons, count = lessons_res.value

    return responses.PaginationResponse(
        data=lessons,
        count=count,
    )


@router.get(
    "/description-file/{lesson_id}",
    dependencies=[
        Depends(check_user_permission({Resources.PUBLISHED_LESSONS: [Actions.READ]})),
    ],
)
def get_published_lesson_description_file_by_id(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):

    lesson_res = queries.get_published_lesson_by_id(lesson_id, request)

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(message="lesson not found", code=404)
        return responses.ApiError(message="failed to get published lesson", Scode=500)

    lesson = lesson_res.value

    if not lesson.description_file:
        return responses.ApiError(message="lesson has no description file", code=404)

    url = GCP_MANAGER.bucket_manager.generate_file_download_url(lesson.description_file)

    return responses.ApiSuccess(data={"url": url})


@router.delete(
    "/{lesson_id}",
    dependencies=[
        Depends(check_user_permission({Resources.PUBLISHED_LESSONS: [Actions.DELETE]}))
    ],
)
def archive_published_lesson_by_id(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):

    tran_res = transactions.archive_published_lesson(request, lesson_id)

    if not tran_res or not tran_res.success:
        return responses.ApiError(
            message="failed to archive published lesson", code=400
        )

    return responses.ApiSuccess(data={"_id": lesson_id})


@router.patch(
    "/{lesson_id}",
    dependencies=[
        Depends(
            check_user_permission({Resources.PUBLISHED_LESSONS: [Actions.DUPPLICATE]})
        )
    ],
)
def duplicate_published_lesson_by_id(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):

    lesson_res = queries.get_published_lesson_by_id(
        lesson_id, request, populate=None, action=Actions.DUPPLICATE
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(message="lesson not found", code=404)
        return responses.ApiError(message="failed to get lesson", code=500)

    lesson = lesson_res.value

    tran_res = transactions.duplicate_published_lesson(request, lesson)

    # TODO improve error handling
    if not tran_res or not tran_res.success:
        return responses.ApiError(message="failed to duplicate lesson", code=400)

    # no need to return the lesson id because each user can have only one draft lesson
    # and you can get the draft lesson by the user id
    return responses.ApiSuccess(message="lesson duplicated successfully")
