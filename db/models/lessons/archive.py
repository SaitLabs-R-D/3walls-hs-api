from .common import BaseLessons
from ..common import DBModel
from typing import Union
from datetime import datetime
from pydantic import Field
from helpers.fields import ObjectIdField
from enum import Enum


class ArchiveLessons(BaseLessons, DBModel):

    archive_at: datetime = Field(default_factory=datetime.utcnow)
    archive_by: Union[ObjectIdField, "Users"] = Field(...)

    class Fields(str, Enum):
        archive_at = "archive_at"
        archive_by = "archive_by"
        id = "_id"
        created_at = "created_at"
        updated_at = "updated_at"
        title_ = "title"
        description = "description"
        creator = "creator"
        description_file = "description_file"
        parts = "parts"
        viewed = "viewed"
        categories = "categories"
        thumbnail = "thumbnail"
        mid_edit = "mid_edit"
        edit_data = "edit_data"
        public = "public"
        credit = "credit"


from ..users import Users

ArchiveLessons.update_forward_refs()
