from fastapi import APIRouter, Depends, Query
from ...middleware import check_user_permission, login_required, Resources, Actions
from helpers.types import RequestWithFullUser, responses
from db import queries, updates
from . import models

router = APIRouter(dependencies=[Depends(login_required)])


@router.get(
    "",
    dependencies=[
        Depends(check_user_permission({Resources.ROLES: [Actions.READ_MANY]})),
    ],
)
def get_roles(
    request: RequestWithFullUser,
    accountable: bool = Query(
        False,
        description="If true, only roles that can be added to account users will be returned",
    ),
    not_accountable: bool = Query(
        False,
        description="If true, only roles that can't be added to account users will be returned",
    ),
):

    roles_res = queries.get_roles_for_external(request, accountable, not_accountable)

    if roles_res.failure:
        return responses.ApiError(
            message="failed to get roles",
            code=500,
        )

    return responses.ApiSuccess(data=roles_res.value)


@router.put(
    # In the future it may be role_id
    "/guest",
    dependencies=[
        Depends(check_user_permission({Resources.ROLES: [Actions.UPDATE]})),
    ],
)
def update_guest_role(
    request: RequestWithFullUser,
    data: models.UpdateRoleLessonContentPayload,
):

    if data.categories is not None:
        query_res = queries.validate_categories_exists(data.categories)

        if query_res.failure:
            return responses.ApiError(message="failed to validate categories", code=500)

    if data.lessons is not None:
        query_res = queries.validate_published_lessons_exists(data.lessons)

        if query_res.failure:
            return responses.ApiError(message="failed to validate lessons", code=500)

    update_res = updates.update_guest_role(data.categories, data.lessons)

    if update_res.failure:
        return responses.ApiError(message="failed to update guest role", code=500)

    return responses.ApiSuccess()


@router.get(
    "/guest",
    dependencies=[
        Depends(check_user_permission({Resources.ROLES: [Actions.READ]})),
    ],
)
def get_guest_role_full_extarnel(
    request: RequestWithFullUser,
):

    query_res = queries.get_guest_role_full_extarnel(request)

    if query_res.failure:
        return responses.ApiError(
            message="failed to update guest role",
            code=500,
        )

    return responses.ApiSuccess(data=query_res.value)
