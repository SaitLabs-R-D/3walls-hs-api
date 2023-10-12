from .common import DBModel, MongoIndex
from pydantic import Field
from helpers import fields
from typing import Optional, Union
from enum import Enum


class SiteHelp(DBModel):
    background_image: Optional[str] = Field(None)
    title: str = Field(...)
    pdf: Optional[str] = Field(None)
    youtube_link: Optional[str] = Field(None)
    # If a category if being deleted, then its possible that the category will be None
    category: Optional[Union[fields.ObjectIdField, "SiteHelpCategories"]] = Field(...)
    description: str = Field(...)
    creator: Union[fields.ObjectIdField, "Users"] = Field(...)
    order: int = Field(...)

    class Fields(str, Enum):
        id = "_id"
        created_at = "created_at"
        updated_at = "updated_at"
        background_image = "background_image"
        title_ = "title"
        pdf = "pdf"
        youtube_link = "youtube_link"
        category = "category"
        description = "description"
        creator = "creator"
        order = "order"


class SiteHelpCategories(DBModel):
    name: str = Field(...)
    description: Optional[str] = Field(None)

    class Fields(str, Enum):
        id = "_id"
        created_at = "created_at"
        updated_at = "updated_at"
        name_ = "name"
        description = "description"

    @classmethod
    def get_indexes(cls) -> list[MongoIndex]:

        unique_name = (
            MongoIndex(
                "unique_name",
            )
            .add_field(cls.Fields.name_, 1)
            .set_unique()
        )

        return [unique_name]


from .users import Users

SiteHelp.update_forward_refs()
