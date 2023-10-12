from datetime import datetime
from ..categories import Categories
import uuid
from typing import Union, Optional
from pydantic import BaseModel, Field
from helpers.fields import ObjectIdField
from enum import Enum
from db.models.common import DBModel


class ScreensTypes(str, Enum):
    VIDEO = "video"
    IMAGE = "img"
    BROWSER = "browser"


class LessonScreen(BaseModel):
    url: Optional[str] = Field(None, description="URL of the screen (gcp path)")
    type_: Optional[ScreensTypes] = Field(None, description="Type of the screen")
    mime_type: Optional[str] = Field(None, description="Mime type of the screen")
    comment: Optional[str] = Field(None)


class LessonPart(BaseModel):
    class Types(str, Enum):
        NORMAL = "normal"
        PANORAMIC = "panoramic"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    order: int = Field(...)
    screens: list[LessonScreen] = Field(
        default_factory=lambda: [LessonScreen(), LessonScreen(), LessonScreen()]
    )
    title: Optional[str] = Field(None, description="Title of the part")
    type_: Types = Field(Types.NORMAL, alias="type")
    gcp_path: Optional[str] = Field(None, description="GCP path of the panoramic image if type is panoramic")
    panoramic_url: Optional[str] = Field(None, description="URL of the panoramic asset if type is panoramic")

    class Config:
        allow_population_by_field_name = True


    def dict(self, *args, **kwargs):
        kwargs["by_alias"] = True
        return super().dict(*args, **kwargs)

    class Fields(str, Enum):
        id = "_id"
        order = "order"
        screens = "screens"
        title_ = "title"
        type_ = "type"
        gcp_path = "gcp_path"
        panoramic_url = "panoramic_url"

    def is_panoramic(self) -> bool:
        return self.type_ == self.Types.PANORAMIC
    
    def is_normal(self) -> bool:
        return self.type_ == self.Types.NORMAL

class LessonEdit(BaseModel):
    initial_editor: Union[ObjectIdField, "Users"] = Field(...)
    current_editor: Union[ObjectIdField, "Users"] = Field(...)
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    description_file: Optional[str] = Field(
        None, description="URL of the description file"
    )
    parts: list[LessonPart] = Field(default_factory=list)
    categories: Union[list[ObjectIdField], list[Categories]] = Field(...)
    thumbnail: Optional[str] = Field(None, description="URL of the thumbnail")
    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the edit started"
    )
    credit: Optional[str] = Field(None)

    def dict(self, *args, **kwargs):
        kwargs["by_alias"] = True
        return super().dict(*args, **kwargs)

    class Fields(str, Enum):
        initial_editor = "initial_editor"
        current_editor = "current_editor"
        title_ = "title"
        description = "description"
        description_file = "description_file"
        parts = "parts"
        categories = "categories"
        thumbnail = "thumbnail"
        started_at = "started_at"
        credit = "credit"

    def get_part_by_id(self, part_id: str) -> Union[LessonPart, None]:
        for part in self.parts:
            if part.id == part_id:
                return part

        return None


class BaseLessons(DBModel):

    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    creator: Union[ObjectIdField, "Users"] = Field(...)
    description_file: Optional[str] = Field(None)
    parts: list[LessonPart] = Field(default_factory=list)
    viewed: int = Field(default=0)
    categories: Union[list[Categories], list[ObjectIdField]] = Field(
        default_factory=list
    )
    thumbnail: Optional[str] = Field(None)
    mid_edit: bool = Field(default=False)
    edit_data: Optional[LessonEdit] = Field(None)
    public: bool = Field(default=False)
    credit: Optional[str] = Field(None)

    def get_part(self, part_id: str) -> Union[None, LessonPart]:

        for part in self.parts:
            if part.id == part_id:
                return part

        return None


class BaseLessonFields(str, Enum):
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

BaseLessons.update_forward_refs()
LessonEdit.update_forward_refs()
