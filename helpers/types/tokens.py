from pydantic import BaseModel, Field
import time, secrets
from typing import TypeVar, Generic, Literal
from datetime import datetime, timedelta


class JwtLoginTokenData(BaseModel):
    user_id: str = Field(...)
    created_at: int = Field(default_factory=time.time)


class FirstLoginTokenData(BaseModel):
    user_id: str = Field(...)
    created_at: int = Field(default_factory=time.time)
    # one week
    exp: int = Field(default_factory=lambda: time.time() + 60 * 60 * 24 * 7)


class ResetPasswordTokenData(BaseModel):
    user_id: str = Field(...)
    created_at: int = Field(default_factory=time.time)
    # one hour
    exp: int = Field(default_factory=lambda: time.time() + 60 * 60)


D = TypeVar("D")


class DecodeTokenResults(Generic[D]):
    def __init__(
        self,
        success: bool = False,
        failure: bool = False,
        expired: bool = False,
        invalid: bool = False,
        value: D = None,
    ):
        self.value = value
        self.success = success
        self.failure = failure
        self.expired = expired
        self.invalid = invalid


class WatchTokenData(BaseModel):
    lesson_id: str = Field(...)
    lesson_type: Literal["draft", "published", "publish-edit"] = Field(...)
    issuer: str = Field(...)
    id: str = Field(default_factory=lambda: secrets.token_hex(16))
    exp: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=1))
