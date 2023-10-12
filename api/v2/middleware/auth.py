from fastapi import Depends, Request
from helpers.exceptions.redirect import RedirectException
from fastapi.security import APIKeyCookie
from helpers.types import Cookeys, RediractsPaths
from services.redis import REDIS_DB
from helpers.secuirty import tokens


login_required_scheme = APIKeyCookie(
    name=Cookeys.ACCESS_TOKEN.value,
    scheme_name="User Access Token",
    description="Token to validate that the user is logged in will be added to the cookies after login",
)


def login_required(request: Request, token: str = Depends(login_required_scheme)):

    if not token:
        raise RedirectException(RediractsPaths.LOGIN.value)

    decoded_token: None

    token_data = tokens.decode_access_token(token)

    if token_data.failure:
        if token_data.expired:
            raise RedirectException(
                RediractsPaths.LOGIN.value, remove_cookies=[Cookeys.ACCESS_TOKEN.value]
            )
        raise RedirectException(
            RediractsPaths.LOGIN.value, remove_cookies=[Cookeys.ACCESS_TOKEN.value]
        )

    # saved_token = REDIS_DB.get_user_login_token(user_id)

    # if not saved_token:
    #     raise RedirectException(
    #         RediractsPaths.LOGIN.value, remove_cookies=[Cookeys.ACCESS_TOKEN.value]
    #     )

    # if not saved_token == token:
    #     raise RedirectException(
    #         RediractsPaths.LOGIN.value, remove_cookies=[Cookeys.ACCESS_TOKEN.value]
    #     )

    request.state.user_id = token_data.value.user_id


def guest_required(request: Request):

    token = request.cookies.get(Cookeys.ACCESS_TOKEN.value)

    if token:
        token_data = tokens.decode_access_token(token)
        if token_data.success:
            raise RedirectException(RediractsPaths.HOME.value)
        else:
            # TODO - remove the cookie
            pass
