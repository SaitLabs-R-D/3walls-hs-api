from pydantic import BaseModel, Field, root_validator
from helpers import fields
from typing import Optional


class CreateAccountPayload(BaseModel):
    institution_name: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    contact_man_first_name: str = Field(..., min_length=1, max_length=100)
    contact_man_last_name: str = Field(..., min_length=1, max_length=100)
    email: fields.EmailField = Field(...)
    phone: fields.PhoneField = Field(...)
    logo: Optional[fields.Base64ImageField] = Field(None)
    allowed_users: int = Field(..., ge=1, le=69420)
    lessons: Optional[set[fields.ObjectIdField]] = Field(None)
    categories: Optional[set[fields.ObjectIdField]] = Field(None)


class UpdateAccountPayload(BaseModel):
    categories: Optional[list[fields.ObjectIdField]] = Field(
        None,
        min_items=0,
        max_items=10000,
        description="list of the updated categories for the account",
    )
    lessons: Optional[list[fields.ObjectIdField]] = Field(
        None,
        min_items=0,
        max_items=10000,
        description="list of the updated lessons for the account",
    )
    email: Optional[fields.EmailField] = Field(None)
    phone: Optional[fields.PhoneField] = Field(None)
    allowed_users: Optional[int] = Field(None, ge=1, le=69420)
    logo: Optional[fields.Base64ImageField] = Field(None)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    institution_name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_man_name: Optional[str] = Field(None, min_length=1, max_length=200)

    @root_validator
    def check_if_nothing_updated(cls, values):
        # some fields can be empty list or 0 so we need to check if any of the values is not None
        if not any([value != None for value in values.values()]):
            raise ValueError("nothing to update")
        return values
