from .common import DBModel, MongoIndex
from pydantic import Field
from enum import Enum
from typing import Union, Optional
from helpers.fields import ObjectIdField


class Accounts(DBModel):
    institution_name: str = Field(...)
    city: str = Field(...)
    contact_man_name: str = Field(...)
    email: str = Field(...)
    phone: str = Field(...)
    logo: Optional[str] = Field(None)
    allowed_users: int = Field(
        ..., description="Number of users allowed to be created for this account"
    )
    allowed_lessons: Union[
        list[ObjectIdField], list["PublishedLessons"], list["ArchiveLessons"]
    ] = Field(default_factory=list)
    allowed_categories: Union[list[ObjectIdField], list["Categories"]] = Field(
        default_factory=list
    )
    current_users: int = Field(
        0, description="Number of existing users for this account"
    )

    def dict(self, to_db: bool = False, *args, **kwargs):
        if to_db:
            self.email = self.email.lower()
        return super().dict(to_db, *args, **kwargs)

    class Fields(str, Enum):
        id = "_id"
        created_at = "created_at"
        updated_at = "updated_at"
        institution_name = "institution_name"
        city = "city"
        contact_man_name = "contact_man_name"
        email = "email"
        phone = "phone"
        logo = "logo"
        allowed_users = "allowed_users"
        allowed_lessons = "allowed_lessons"
        allowed_categories = "allowed_categories"
        current_users = "current_users"

    @classmethod
    def get_indexes(cls) -> list[MongoIndex]:

        unique_institution_in_city = (
            MongoIndex(
                "unique_institution_in_city",
            )
            .add_field(cls.Fields.institution_name, 1)
            .add_field(cls.Fields.city, 1)
            .set_unique()
        )

        return [unique_institution_in_city]


from .lessons.published import PublishedLessons
from .lessons.archive import ArchiveLessons
from .categories import Categories

Accounts.update_forward_refs()
