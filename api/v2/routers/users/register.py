from fastapi import APIRouter, Depends, BackgroundTasks
from ...middleware import (
    guest_required,
    login_required,
    check_user_permission,
    Actions,
    Resources,
)
from . import models
from db import queries, inserts, updates
from helpers.types import responses, RequestWithFullUser
from helpers.secuirty import tokens, passwords
from services.sendgrid import EMAIL_SERVICE
from helpers import cookies

router = APIRouter()


@router.post("/guest", dependencies=[Depends(guest_required)])
def register_as_guest(data: models.RegisterAsGuestPayload):

    guest_role = queries.get_guest_role()

    if guest_role.failure or guest_role.not_found:
        return guest_role.into_response()

    # TODO change to transaction
    user_res = inserts.insert_new_guest_user(
        guest_role=guest_role.value,
        email=data.email,
        password=passwords.hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
    )

    if user_res.failure or user_res.exists:
        return user_res.into_response()

    user = user_res.value

    token = tokens.generate_registration_token(str(user.id))

    update_res = updates.set_user_registration_token(user.id, token)

    if update_res.failure:
        return responses.ApiError()

    EMAIL_SERVICE.send_email_verification_mail(
        user.email, user.email, user.full_name, token, True
    )

    return responses.ApiSuccess()


@router.put("/verify", dependencies=[Depends(guest_required)])
def verify_registration(data: models.VerifyRegistrationPayload):

    token_data = tokens.decode_registration_token(data.token)

    if token_data.failure:
        if token_data.expired:
            return responses.ApiError(
                message="token expired",
                code=400,
            )
        return responses.ApiError(
            message="invalid token",
            code=400,
        )

    user_res = updates.set_user_registration_completed(
        token_data.value.user_id, data.token
    )

    if user_res.failure or user_res.not_found:
        return user_res.into_response()

    user = queries.get_user_for_get_me(user_res.value.id)

    res = responses.ApiSuccess(data=user.value)

    cookies.set_user_access_token(res, user_res.value)

    return res


@router.put(
    "/",
    dependencies=[
        Depends(login_required),
        Depends(check_user_permission({Resources.USERS: [Actions.CREATE]})),
    ],
)
def register_new_user(
    request: RequestWithFullUser,
    data: models.RegisterUserPayload,
    background_tasks: BackgroundTasks,
):

    account = data.account or request.state.user.account

    if account:
        account_res = queries.check_account_user_limit(account)

        if account_res.failure:
            return responses.ApiError(
                message="failed to check account user limit",
                code=500,
            )

        if account_res.value:
            return responses.ApiError(
                message="account user limit reached",
                code=400,
            )

    role_res = queries.get_role_by_id(data.role, request)

    if role_res.failure:
        if not role_res.not_found:
            return responses.ApiError(
                message="role not found",
                code=400,
            )
        return responses.ApiError(
            message="failed to get role",
            code=500,
        )

    if role_res.value.require_account and not account:
        return responses.ApiError(
            message="role can't be added to users without account",
            code=400,
        )
    elif not role_res.value.require_account and account:
        return responses.ApiError(
            message="role can't be added to users with account",
            code=400,
        )

    user_res = inserts.insert_new_user(
        request=request,
        email=data.email,
        password=passwords.hash_password(passwords.generate_password()),
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        account=account,
        phone_number=data.phone_number,
    )

    if user_res.failure:
        if user_res.exists:
            return responses.ApiError(
                message="user already exists",
                code=409,
            )
        if user_res.not_valid:
            return responses.ApiError(
                message="invalid data",
                code=400,
            )

        return responses.ApiError(
            message="failed to create user",
            code=500,
        )

    user = user_res.value

    def send_user_created_mail(user):

        if updates.update_account_current_users_count(user.account, 1).failure:
            # TODO log error
            pass

        token = tokens.generate_first_login_token(str(user.id))

        update_res = updates.set_user_registration_token(user.id, token)

        if update_res.failure:
            # TODO log error
            return

        EMAIL_SERVICE.send_regstration_email(
            user.email, user.email, user.full_name, token
        )

    background_tasks.add_task(send_user_created_mail, user)

    return responses.ApiSuccess()
