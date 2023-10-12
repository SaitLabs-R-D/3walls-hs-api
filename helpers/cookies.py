from helpers.types import Cookeys, CookiesExpiration
from fastapi import Response
from db.models import Users
from helpers.secuirty import tokens
from helpers.env import EnvVars


def remove_user_access_token(response: Response) -> None:

    response.delete_cookie(key=Cookeys.ACCESS_TOKEN.value, domain=EnvVars.COOKIE_DOMAIN)


def set_user_access_token(response: Response, user: Users) -> None:

    response.set_cookie(
        key=Cookeys.ACCESS_TOKEN.value,
        value=tokens.generate_access_token(str(user.id)),
        httponly=True,
        max_age=CookiesExpiration.ACCESS_TOKEN.value,
        domain=EnvVars.COOKIE_DOMAIN or None,
    )
