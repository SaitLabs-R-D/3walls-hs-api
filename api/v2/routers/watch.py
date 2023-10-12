from fastapi import APIRouter, Path, Depends, Query, BackgroundTasks
from ..middleware import check_user_permission, login_required, Actions, Resources
from helpers.types import RequestWithFullUser, responses
from helpers import fields
from db import queries, updates
from db.models.lessons.common import LessonScreen, LessonPart
from helpers.secuirty import tokens
from services.gcp import GCP_MANAGER
from datetime import timedelta
from bson import ObjectId

router = APIRouter()


@router.get(
    "/token/draft",
    dependencies=[
        Depends(login_required),
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.READ]})),
    ],
)
def get_watch_token_for_draft_lesson(request: RequestWithFullUser):

    draft_res = queries.get_draft_lesson_by_creator(request.state.user_id)

    if draft_res.failure:
        if draft_res.not_found:
            return responses.ApiError(
                message="draft lesson not found",
                code=404,
            )
        return responses.ApiError(code=500, message="failed to get draft lesson")

    return responses.ApiSuccess(
        data={
            "token": tokens.generate_watch_token(
                str(draft_res.value.id), "draft", request.state.user_id
            )
        }
    )


@router.get(
    "/token/published/{lesson_id}",
    dependencies=[
        Depends(login_required),
        Depends(
            check_user_permission(
                {
                    Resources.PUBLISHED_LESSONS: [Actions.READ],
                }
            )
        ),
    ],
)
def get_watch_token_for_published_lesson(
    request: RequestWithFullUser,
    background_tasks: BackgroundTasks,
    lesson_id: fields.ObjectIdField = Path(...),
):

    lesson_res = queries.get_published_lesson_by_id(lesson_id, request=request)

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                message="lesson not found",
                code=404,
            )
        return responses.ApiError(code=500, message="failed to get lesson")

    background_tasks.add_task(updates.add_view_to_published_lesson, lesson_id)

    token = tokens.generate_watch_token(
        str(lesson_id), "published", request.state.user_id
    )

    return responses.ApiSuccess(data={"token": token})


@router.get(
    "/token/published-edit/{lesson_id}",
    dependencies=[
        Depends(login_required),
        Depends(
            check_user_permission(
                {
                    Resources.PUBLISHED_LESSONS: [Actions.UPDATE],
                }
            )
        ),
    ],
)
def get_watch_token_for_published_lesson_edit(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):

    user_id = ObjectId(request.state.user_id)

    lesson_res = queries.get_published_lesson_by_id(
        lesson_id, request=request, action=Actions.UPDATE
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                message="lesson not found",
                code=404,
            )

        return responses.ApiError(code=500, message="failed to get lesson")

    lesson = lesson_res.value

    if not lesson.mid_edit:
        return responses.ApiError(
            message="lesson is not mid edit",
            code=400,
        )

    token = tokens.generate_watch_token(
        str(lesson_id), "publish-edit", request.state.user_id
    )

    return responses.ApiSuccess(data={"token": token})


@router.get("/data")
def get_watch_data(token: str = Query(..., min_length=1)):

    token_res = tokens.decode_watch_token(token)

    if token_res.failure:
        return responses.ApiError(code=403, message="Invalid token")

    token_data = token_res.value

    edit_lesson = False

    if token_data.lesson_type == "draft":
        lesson_res = queries.get_draft_lesson_by_id(token_data.lesson_id)
    elif token_data.lesson_type == "published":
        lesson_res = queries.get_published_lesson_by_id(token_data.lesson_id)
    elif token_data.lesson_type == "publish-edit":
        edit_lesson = True
        lesson_res = queries.get_published_lesson_by_id(token_data.lesson_id)
    else:
        return responses.ApiError(message="?")

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                message="lesson not found",
                code=404,
            )
        return responses.ApiError(code=500, message="failed to get lesson")

    lesson = lesson_res.value

    if edit_lesson and not lesson.mid_edit:
        return responses.ApiError(
            message="lesson is not mid edit",
            code=400,
        )

    lesson_parts: list[LessonPart] = (
        lesson.parts if not edit_lesson else lesson.edit_data.parts
    )

    data: list[dict] = []

    for part in lesson_parts:
        screens: list[LessonScreen] = part.screens
        if part.gcp_path:
            part.gcp_path = GCP_MANAGER.bucket_manager.generate_file_download_url(
                part.gcp_path, expiration=timedelta(days=2)
            )
        for screen in screens:
            if screen.mime_type:
                screen.url = GCP_MANAGER.bucket_manager.generate_file_download_url(
                    screen.url, expiration=timedelta(days=2)
                )
        data.append(part.dict())

    return responses.ApiSuccess(data=data)
