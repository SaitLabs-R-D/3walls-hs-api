from .common import BaseLessons, LessonPart, LessonScreen, BaseLessonFields, LessonEdit
from ..common import DBModel, MongoIndex
from typing import Union
from bson import ObjectId
from services.gcp import GCP_MANAGER
from enum import Enum


class PublishedLessons(BaseLessons, DBModel):
    class Fields(str, Enum):
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

    @classmethod
    def get_indexes(cls) -> list[MongoIndex]:

        text_search = (
            MongoIndex(
                "text_search",
            )
            .add_field(cls.Fields.title_, "text")
            .add_field(cls.Fields.description, "text")
        )

        return [text_search]

