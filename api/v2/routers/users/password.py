from fastapi import APIRouter, Depends
from . import models
from db import queries, updates
from ...middleware import login_required, guest_required
from helpers.secuirty import passwords
from helpers.types import responses, RequestWithUserId
from helpers.secuirty import tokens
from services.sendgrid import EMAIL_SERVICE

router = APIRouter()


@router.put("/change", dependencies=[Depends(login_required)])
def change_password(req: RequestWithUserId, data: models.ChangePasswordPayload):

    user = queries.get_user_by_id(req.state.user_id)

    if not user.success:
        return responses.ApiError(code=400, message="user not found")

    user = user.value

    if not passwords.check_password(user.password, data.old_password):
        return responses.ApiError(code=403, message="wrong password")

    db_res = updates.update_user_by_id(
        user.id, password=passwords.hash_password(data.new_password)
    )

    if not db_res.success:
        return responses.ApiError(code=400, message="error while changing password")

    return responses.ApiSuccess(message="password changed successfully")


@router.patch("/reset", dependencies=[Depends(guest_required)])
def request_password_reset(payload: models.RequestPasswordResetPayload):

    user_res = queries.get_user_by_email(payload.email)

    maybe_sent_res = responses.ApiSuccess(
        message="password reset email sent or not sent"
    )

    if user_res.failure:
        if user_res.not_found:
            return maybe_sent_res
        return responses.ApiError(message="something went wrong", code=500)

    token = tokens.generate_reset_password_token(str(user_res.value.id))

    update_res = updates.update_user_by_id(
        user_res.value.id,
        reset_password_token=token,
    )

    if update_res.failure:
        return responses.ApiError(message="something went wrong", code=500)

    EMAIL_SERVICE.send_reset_password(
        payload.email,
        user_res.value.full_name,
        token,
    )

    return maybe_sent_res
