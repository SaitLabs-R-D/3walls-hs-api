from pydantic import BaseModel, Field, root_validator, dataclasses
from helpers import fields
from typing import Optional
from db.models.lessons.common import ScreensTypes, LessonPart
from fastapi import Form, File, UploadFile

class EditDraftLessonBasicInfoPayload(BaseModel):
    title: Optional[str] = Field(None, max_length=41)
    description: Optional[str] = Field(None, max_length=131)
    categories: Optional[list[fields.ObjectIdField]] = Field(None)
    thumbnail: Optional[fields.Base64ImageField] = Field(None)
    description_file: Optional[fields.Base64PdfField] = Field(None)
    credit: Optional[str] = Field(None, max_length=41)

    @root_validator
    def need_some_value(cls, values):
        if (
            not any(values.values())
            and values.get("categories") is None
            and values.get("credit") is None
        ):
            raise ValueError("No data provided")

        return values


class AddPartPayload(BaseModel):
    new_part_order: int = Field(..., ge=0)
    old_parts_order: dict[str, int] = Field(default_factory=dict)
    part_type: LessonPart.Types = Field(LessonPart.Types.NORMAL)

class UpdatePartDataPayload(BaseModel):
    part_id: str = Field(...)
    screen: int = Field(..., ge=0, le=2)
    type_: ScreensTypes = Field(...)
    # It can be part of the url or the whole url
    # so don't validate it
    url: str = Field(...)
    media: bool = Field(default=False)
    comment: str = Field(default=None)

class EditPublishedLessonBasicInfoPayload(EditDraftLessonBasicInfoPayload):
    pass

@dataclasses.dataclass
class UpdatePartPanoramicPayload:
    part_id: str = Form(...)
    image: Optional[UploadFile] = File(None)
    panoramic_url: Optional[fields.URLField] = Form(None)
    