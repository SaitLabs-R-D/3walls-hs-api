from fastapi import APIRouter, Path, Depends
from ...middleware import check_user_permission, pagintor, Actions, Resources
from helpers import fields
from helpers.types import (
    RequestWithPaginationAndFullUser,
    RequestWithFullUser,
    responses,
)
from db import queries, transactions


router = APIRouter()


@router.get(
    "",
    dependencies=[
        Depends(pagintor),
        Depends(
            check_user_permission({Resources.ARCHIVED_LESSONS: [Actions.READ_MANY]})
        ),
    ],
)
def get_archived_lessons(request: RequestWithPaginationAndFullUser):

    archive_res = queries.get_archived_lessons_for_external(request)

    if archive_res.failure:
        return responses.ApiError(
            message="failed to get archived lessons",
            code=500,
        )

    return responses.PaginationResponse(
        data=archive_res.value[0],
        count=archive_res.value[1],
    )


@router.put(
    "/{lesson_id}",
    dependencies=[
        # maybe add a action for restore for now we can use update
        Depends(check_user_permission({Resources.ARCHIVED_LESSONS: [Actions.UPDATE]}))
    ],
)
def restore_archived_lesson_by_id(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):

    lesson_res = queries.get_archive_lesson_by_id(lesson_id, request=request)

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                message="lesson not found",
                code=404,
            )
        return responses.ApiError(
            message="failed to get lesson",
            code=500,
        )

    lesson = lesson_res.value

    lesson_res = transactions.restore_archived_lesson(lesson)

    if lesson_res is None or not lesson_res.success:
        return responses.ApiError(
            message="failed to restore lesson",
            code=500,
        )

    return responses.ApiSuccess(message="lesson restored")


@router.delete(
    "/{lesson_id}",
    dependencies=[
        Depends(check_user_permission({Resources.ARCHIVED_LESSONS: [Actions.DELETE]}))
    ],
)
def delete_archived_lesson_by_id(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):
    # only one role for now can delete archived lessons
    # so there is no need to check for permissions
    lesson_res = transactions.delete_archived_lesson(lesson_id)

    if lesson_res is None or not lesson_res.success:
        return responses.ApiError(
            message="failed to delete lesson",
            code=500,
        )

    return responses.ApiSuccess(message="lesson deleted")
