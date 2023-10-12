from helpers.env import EnvVars
import jwt, os, secrets
from itsdangerous import URLSafeSerializer
from itsdangerous.exc import SignatureExpired
from helpers.types import tokens
from datetime import datetime, timedelta
from typing import Union, Literal


HS256 = "HS256"

registration_token_s = URLSafeSerializer(EnvVars.REGISTRATION_TOKEN_SECRET)
reset_password_token_s = URLSafeSerializer(EnvVars.RESET_PASSWORD_SECRET)
first_login_token_s = URLSafeSerializer(EnvVars.FIRST_LOGIN_SECRET)


def generate_registration_token(user_id: str) -> str:
    data = tokens.FirstLoginTokenData(user_id=user_id).dict()
    return registration_token_s.dumps(data)


def decode_registration_token(
    token: str,
) -> tokens.DecodeTokenResults[tokens.FirstLoginTokenData]:
    try:
        data = registration_token_s.loads(token)
        return tokens.DecodeTokenResults(
            value=tokens.FirstLoginTokenData(**data), success=True
        )
    except SignatureExpired:
        return tokens.DecodeTokenResults(failure=True, expired=True)
    except:
        return tokens.DecodeTokenResults(failure=True, invalid=True)


def generate_access_token(user_id: str) -> str:
    return jwt.encode(
        tokens.JwtLoginTokenData(user_id=user_id).dict(),
        EnvVars.LOGIN_TOKEN_SECRET,
        algorithm=HS256,
    )


def decode_access_token(
    token: str,
) -> tokens.DecodeTokenResults[tokens.JwtLoginTokenData]:
    try:
        data = tokens.JwtLoginTokenData(
            **jwt.decode(token, EnvVars.LOGIN_TOKEN_SECRET, algorithms=[HS256])
        )
        return tokens.DecodeTokenResults(value=data, success=True)
    except jwt.ExpiredSignatureError:
        return tokens.DecodeTokenResults(failure=True, expired=True)
    except:
        return tokens.DecodeTokenResults(failure=True, invalid=True)


def generate_reset_password_token(user_id: str) -> str:
    data = tokens.ResetPasswordTokenData(user_id=user_id).dict()
    return reset_password_token_s.dumps(data)


def decode_reset_password_token(
    token: str,
) -> tokens.DecodeTokenResults[tokens.ResetPasswordTokenData]:
    try:
        data = reset_password_token_s.loads(token)
        return tokens.DecodeTokenResults(
            value=tokens.ResetPasswordTokenData(**data), success=True
        )
    except SignatureExpired:
        return tokens.DecodeTokenResults(failure=True, expired=True)
    except:
        return tokens.DecodeTokenResults(failure=True, invalid=True)


def decode_registration_token_even_if_expired(
    token: str,
) -> tokens.DecodeTokenResults[tokens.FirstLoginTokenData]:
    try:
        data = registration_token_s.loads_unsafe(token)
        return tokens.DecodeTokenResults(
            value=tokens.FirstLoginTokenData(**data[1]), success=True
        )
    except SignatureExpired:
        return tokens.DecodeTokenResults(failure=True, expired=True)
    except:
        return tokens.DecodeTokenResults(failure=True, invalid=True)


def generate_first_login_token(user_id: str) -> str:
    data = tokens.FirstLoginTokenData(user_id=user_id).dict()
    return first_login_token_s.dumps(data)


def decode_first_login_token(
    token: str,
) -> tokens.DecodeTokenResults[tokens.FirstLoginTokenData]:
    try:
        data = first_login_token_s.loads(token)
        return tokens.DecodeTokenResults(
            value=tokens.FirstLoginTokenData(**data), success=True
        )
    except SignatureExpired:
        return tokens.DecodeTokenResults(failure=True, expired=True)
    except:
        return tokens.DecodeTokenResults(failure=True, invalid=True)


def generate_watch_token(
    lesson_id: str,
    lesson_type: Literal["draft", "published", "publish-edit"],
    issuer: str,
) -> str:

    token_data = tokens.WatchTokenData(
        lesson_id=lesson_id, lesson_type=lesson_type, issuer=issuer
    )

    return jwt.encode(
        token_data.dict(),
        EnvVars.WATCH_TOKEN_SECRET,
        algorithm=HS256,
    )


def decode_watch_token(token: str) -> tokens.DecodeTokenResults[tokens.WatchTokenData]:
    try:
        return tokens.DecodeTokenResults(
            success=True,
            value=tokens.WatchTokenData(
                **jwt.decode(token, EnvVars.WATCH_TOKEN_SECRET, algorithms=["HS256"])
            ),
        )
    except jwt.ExpiredSignatureError:
        return tokens.DecodeTokenResults(failure=True, expired=True)
    except:
        return tokens.DecodeTokenResults(failure=True, invalid=True)
