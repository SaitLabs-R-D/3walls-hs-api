from .common import BaseLessons, LessonPart, LessonScreen
from ..common import MongoIndex
from enum import Enum


class DraftLessons(BaseLessons):
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

    # In the draft collection, each user can only have one draft lesson
    # so the creator field is unique only for this collection
    @classmethod
    def get_indexes(cls) -> list[MongoIndex]:

        unique_creator = (
            MongoIndex(
                "unique_creator",
            )
            .add_field(cls.Fields.creator, 1)
            .set_unique()
        )

        return [unique_creator]
