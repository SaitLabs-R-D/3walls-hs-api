from .common import DBModel, MongoIndex
from pydantic import Field
from typing import Optional, Union
from helpers.fields import ObjectIdField
from enum import Enum


class Users(DBModel):
    # each user can be associated with only one account
    # some users may not have an account
    account: Optional[Union[ObjectIdField, "Accounts"]] = Field(None)
    email: str = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    full_name: str = Field(None)
    role: Union["Roles", ObjectIdField] = Field(...)
    password: str = Field(...)
    phone_number: Optional[str] = Field(None)
    allowed_lessons: Union[
        list[ObjectIdField], list["PublishedLessons"], list["ArchiveLessons"]
    ] = Field(default_factory=list)
    allowed_categories: Union[list[ObjectIdField], list["Categories"]] = Field(
        default_factory=list
    )
    registration_token: str = Field(None)
    registration_completed: bool = Field(False)
    reset_password_token: str = Field(None)

    @classmethod
    def get_indexes(cls) -> list[MongoIndex]:

        uniuqe_email = (
            MongoIndex(
                "unique_email",
            )
            .add_field(cls.Fields.email, 1)
            .set_unique()
        )

        return [uniuqe_email]

    def dict(self, to_db: bool = False, *args, **kwargs):
        if to_db:
            self.full_name = f"{self.first_name} {self.last_name}"
            self.email = self.email.lower()
        return super().dict(to_db, *args, **kwargs)

    class Fields(str, Enum):
        id = "_id"
        created_at = "created_at"
        updated_at = "updated_at"
        account = "account"
        email = "email"
        first_name = "first_name"
        last_name = "last_name"
        full_name = "full_name"
        phone_number = "phone_number"
        role = "role"
        password = "password"
        allowed_lessons = "allowed_lessons"
        allowed_categories = "allowed_categories"
        registration_token = "registration_token"
        registration_completed = "registration_completed"
        reset_password_token = "reset_password_token"


from .accounts import Accounts
from .categories import Categories
from .roles import Roles
from .lessons.published import PublishedLessons
from .lessons.archive import ArchiveLessons

Users.update_forward_refs()
