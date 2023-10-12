from fastapi import APIRouter, Depends, Path, BackgroundTasks
from ...middleware import (
    login_required,
    check_user_permission,
    Actions,
    Resources,
    pagintor,
)
from helpers.types import (
    responses,
    RequestWithUserId,
    RequestWithFullUser,
    RequestWithPaginationAndFullUser,
    UserPopulateOptions,
)
from db import queries, updates, transactions
from . import register, login, password, models, logout
from helpers import fields

router = APIRouter()

router.include_router(register.router, prefix="/register")
router.include_router(login.router, prefix="/login")
router.include_router(logout.router, prefix="/logout")
router.include_router(password.router, prefix="/password")


@router.get("/me", dependencies=[Depends(login_required)])
def get_me(request: RequestWithUserId):
    user = queries.get_user_for_get_me(request.state.user_id)

    if user.failure:
        if user.not_found:
            # TODO delete token
            return responses.ApiError(
                message="user not found",
                code=404,
            )
        return responses.ApiError()

    return responses.ApiSuccess(data=user.value)


@router.get(
    "",
    dependencies=[
        Depends(login_required),
        Depends(pagintor),
        Depends(check_user_permission({Resources.USERS: [Actions.READ_MANY]})),
    ],
)
def get_users(
    request: RequestWithPaginationAndFullUser,
    query: models.GetUsersQueryParams = Depends(),
):
    if query.guests:
        guest_role = queries.get_guest_role()

        if guest_role.failure:
            return responses.ApiError(
                message="guest role not found",
                code=500,
            )

        query.role = guest_role.value.id

    users_res = queries.get_users_for_external(
        request,
        query.role,
        query.account,
    )

    if users_res.failure:
        return responses.ApiError(
            message="failed to get users",
            code=500,
        )

    users, count = users_res.value

    return responses.PaginationResponse(
        data=users,
        count=count,
    )


@router.get(
    "/{user_id}",
    dependencies=[
        Depends(login_required),
        Depends(check_user_permission({Resources.USERS: [Actions.READ]})),
    ],
)
def get_user_by_id(
    request: RequestWithFullUser,
    user_id: str,
):
    user_res = queries.get_user_by_id_for_external(request, user_id)

    if user_res.failure:
        if user_res.not_found:
            return responses.ApiError(
                message="user not found",
                code=404,
            )
        return responses.ApiError(
            message="failed to get user",
            code=500,
        )

    return responses.ApiSuccess(data=user_res.value)


@router.put(
    "/{user_id}",
    dependencies=[
        Depends(login_required),
        Depends(
            check_user_permission(
                {Resources.USERS: [Actions.UPDATE], Resources.ROLES: [Actions.READ]}
            )
        ),
    ],
)
def update_user_by_id(
    request: RequestWithFullUser,
    payload: models.UpdateUserPayload,
    user_id: fields.ObjectIdField = Path(...),
):
    if payload.lessons:
        check_lessons_result = queries.validate_published_lessons_exists(
            payload.lessons
        )
        if check_lessons_result.failure:
            if check_lessons_result.not_found:
                return responses.ApiError(code=404, message="lessons not found")
            return responses.ApiError(code=500, message="error while checking lessons")

    if payload.categories:
        check_categories_result = queries.validate_categories_exists(payload.categories)
        if check_categories_result.failure:
            if check_categories_result.not_found:
                return responses.ApiError(code=404, message="categories not found")
            return responses.ApiError(
                code=500, message="error while checking categories"
            )

    account_need_to_be_null = False

    if payload.role:
        if request.state.user_id == user_id:
            return responses.ApiError(
                code=400, message="you can't change your own role"
            )
        check_role_result = queries.get_role_by_id(payload.role, request)
        if check_role_result.failure:
            if check_role_result.not_found:
                return responses.ApiError(code=404, message="role not found")
            return responses.ApiError(code=500, message="error while checking role")
        if not check_role_result.value.require_account:
            account_need_to_be_null = True

    updates_res = updates.update_user_by_id(
        user_id,
        request=request,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        allowed_lessons=payload.lessons,
        allowed_categories=payload.categories,
        phone_number=payload.phone_number,
        account_need_to_be_null=account_need_to_be_null,
    )

    if updates_res.failure:
        if updates_res.not_found:
            return responses.ApiError(code=404, message="user not found")
        if updates_res.not_valid:
            return responses.ApiError(code=400, message="invalid data")
        if updates_res.exists:
            return responses.ApiError(code=409, message="duplicate data")
        return responses.ApiError(code=500, message="error while updating user")

    return responses.ApiSuccess(message="user updated successfully")


@router.delete(
    "/{user_id}",
    dependencies=[
        Depends(login_required),
        Depends(check_user_permission({Resources.USERS: [Actions.DELETE]})),
    ],
)
def delete_user_by_id(
    request: RequestWithFullUser,
    background_tasks: BackgroundTasks,
    user_id: fields.ObjectIdField = Path(...),
):
    if request.state.user_id == str(user_id):
        return responses.ApiError(code=400, message="you can't delete yourself")

    user_res = queries.get_user_by_id(
        user_id,
        populate=UserPopulateOptions(
            role=True,
        ),
        request=request,
    )

    if user_res.failure:
        if user_res.not_found:
            return responses.ApiError(code=404, message="user not found")
        return responses.ApiError(code=500, message="error while getting user")

    background_tasks.add_task(transactions.fully_delete_user, user_id, request)

    return responses.ApiSuccess(message="user deleted successfully")
