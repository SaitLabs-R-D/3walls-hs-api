from .common import DBModel, MongoIndex
from pydantic import Field
from typing import Optional
from enum import Enum


class Categories(DBModel):
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

        text_search = (
            MongoIndex(
                "text_search",
            )
            .add_field(cls.Fields.name_, "text")
            .add_field(cls.Fields.description, "text")
        )

        return [unique_name, text_search]
