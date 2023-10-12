from fastapi import APIRouter, Depends
from db import queries, updates
from ...middleware import (
    guest_required,
)
from . import models
from helpers.secuirty import passwords, tokens
from helpers.types import responses
from helpers import cookies


router = APIRouter(dependencies=[Depends(guest_required)])


@router.post("")
def login(data: models.UserLoginPayload):

    user_res = queries.get_user_by_email(data.email)

    user_not_found_response = responses.ApiError(
        message="wrong email or password",
        code=404,
    )

    if user_res.failure:
        if user_res.not_found:
            return user_not_found_response
        return responses.ApiError(message="something went wrong", code=500)

    user = user_res.value

    if not passwords.check_password(user.password, data.password):
        return user_not_found_response

    get_me_res = queries.get_user_for_get_me(user.id)

    if get_me_res.failure:
        if get_me_res.not_found:
            return user_not_found_response
        return responses.ApiError(message="something went wrong", code=500)

    res = responses.ApiSuccess(data=get_me_res.value)

    cookies.set_user_access_token(res, user_res.value)

    return res


@router.post("/first")
def first_login(data: models.FirstLoginPayload):

    token_res = tokens.decode_first_login_token(data.token)

    if token_res.failure:
        if token_res.expired:
            return responses.ApiError(message="token expired", code=400)
        return responses.ApiError(message="invalid token", code=400)

    token_data = token_res.value

    user_res = updates.set_user_registration_completed(
        token_data.user_id,
        data.token,
        passwords.hash_password(data.password),
    )

    if user_res.failure:
        if user_res.not_found:
            return responses.ApiError(message="invalid token", code=400)
        return responses.ApiError(message="something went wrong", code=500)

    user = user_res.value

    get_me_res = queries.get_user_for_get_me(user.id)

    if get_me_res.failure:
        return responses.ApiError(message="something went wrong", code=500)

    res = responses.ApiSuccess(data=get_me_res.value)

    cookies.set_user_access_token(res, user_res.value)

    return res


@router.post("/reset")
def login_with_reset_password_token(payload: models.ResetPasswordPayload):

    token_res = tokens.decode_reset_password_token(payload.token)

    if token_res.failure:
        if token_res.expired:
            return responses.ApiError(message="token expired", code=400)
        return responses.ApiError(message="invalid token", code=400)

    token_data = token_res.value

    user_res = updates.change_user_password_with_token(
        token_data.user_id,
        payload.token,
        password=passwords.hash_password(payload.password),
    )

    if user_res.failure:
        if user_res.not_found:
            return responses.ApiError(message="invalid token", code=400)
        return responses.ApiError(message="something went wrong", code=500)

    user = user_res.value

    get_me_res = queries.get_user_for_get_me(user.id)

    if get_me_res.failure:
        return responses.ApiError(message="something went wrong", code=500)

    res = responses.ApiSuccess(data=get_me_res.value)

    cookies.set_user_access_token(res, user_res.value)

    return res
