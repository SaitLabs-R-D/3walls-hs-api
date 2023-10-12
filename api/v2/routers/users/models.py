from pydantic import BaseModel, Field, root_validator
from helpers import fields
from typing import Optional


class RegisterAsGuestPayload(BaseModel):
    email: fields.EmailField = Field(...)
    password: fields.PasswordField = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)


class VerifyRegistrationPayload(BaseModel):
    token: str = Field(...)


class UserLoginPayload(BaseModel):
    email: fields.EmailField = Field(...)
    password: fields.PasswordField = Field(...)


class ChangePasswordPayload(BaseModel):
    old_password: fields.PasswordField = Field(...)
    new_password: fields.PasswordField = Field(...)


class FirstLoginPayload(BaseModel):
    password: fields.PasswordField = Field(...)
    token: str = Field(...)


class RegisterUserPayload(BaseModel):
    email: fields.EmailField = Field(...)
    phone_number: Optional[fields.PhoneField] = Field(None)
    first_name: str = Field(...)
    last_name: str = Field(...)
    role: fields.ObjectIdField = Field(...)
    account: Optional[fields.ObjectIdField] = Field(None)


class GetUsersQueryParams(BaseModel):
    guests: bool = Field(False)
    role: Optional[fields.ObjectIdField] = Field(None)
    account: Optional[fields.ObjectIdField] = Field(None)
    # search: Optional[str] = Field(None)

    @root_validator
    def validate_role_and_guest(cls, values):
        if values.get("role") and values.get("guests"):
            raise ValueError("role and quests cannot be used together")
        return values


class UpdateUserPayload(BaseModel):
    categories: Optional[list[fields.ObjectIdField]] = Field(
        None,
        min_items=0,
        max_items=10000,
        description="list of the updated categories for the user",
    )
    lessons: Optional[list[fields.ObjectIdField]] = Field(
        None,
        min_items=0,
        max_items=10000,
        description="list of the updated lessons for the user",
    )
    email: Optional[fields.EmailField] = Field(None)
    phone_number: Optional[fields.PhoneField] = Field(None)
    role: Optional[fields.ObjectIdField] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)

    @root_validator
    def check_if_nothing_updated(cls, values):
        # some fields can be empty list or 0 so we need to check if any of the values is not None
        if not any([value != None for value in values.values()]):
            raise ValueError("nothing to update")
        return values


class RequestPasswordResetPayload(BaseModel):
    email: fields.EmailField = Field(...)


class ResetPasswordPayload(BaseModel):
    token: str = Field(...)
    password: fields.PasswordField = Field(...)
