from pydantic import BaseModel, Field, root_validator
from helpers import fields
from typing import Optional


class UpdateRoleLessonContentPayload(BaseModel):
    categories: Optional[list[fields.ObjectIdField]] = Field(None)
    lessons: Optional[list[fields.ObjectIdField]] = Field(None)

    @root_validator
    def validate_categories_or_lessons(cls, values):
        categories = values.get("categories")
        lessons = values.get("lessons")

        if categories is None and lessons is None:
            raise ValueError("categories or lessons must be provided")

        return values
