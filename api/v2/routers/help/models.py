from pydantic import Field, BaseModel, root_validator
from typing import Optional, Union, Literal
from helpers import fields


class GetSiteHelpQueryParams(BaseModel):
    category: Optional[fields.ObjectIdField] = Field(None, alias="category")
    list_view: bool = Field(False, alias="list_view")


class NewSiteHelpPayload(BaseModel):
    background_image: fields.Base64ImageField = Field(...)
    title: str = Field(...)
    pdf: Optional[fields.Base64PdfField] = Field(None)
    youtube_link: Optional[fields.URLField] = Field(None)
    category: fields.ObjectIdField = Field(...)
    description: str = Field(...)


class NewSiteHelpCategoryPayload(BaseModel):
    name: str = Field(...)
    description: str = Field(...)


class UpdateSiteHelpCategorPayload(BaseModel):
    name: Union[str, None] = Field(None, min_length=2, max_length=50)
    description: Union[str, None] = Field(None, max_length=200)

    @root_validator
    def check_if_any_field_is_not_none(cls, values):
        if not any([values.get("name"), values.get("description")]):
            raise ValueError("at least one field must be provided")
        return values


class EditSiteHelpPayload(BaseModel):
    background_image: Optional[fields.Base64ImageField] = Field(None)
    title: Optional[str] = Field(None, max_length=41)
    pdf: Optional[fields.Base64PdfField] = Field(None)
    # empty string to remove youtube link
    youtube_link: Optional[Union[Literal[""], fields.URLField]] = Field(None)
    description: Optional[str] = Field(None)
    category: Optional[fields.ObjectIdField] = Field(None)

    @root_validator
    def need_some_value(cls, values):
        if not any(values.values()) and not values.get("youtube_link") == "":
            raise ValueError("No data provided")

        return values


class ReorderSiteHelpPayload(BaseModel):
    site_help_id: fields.ObjectIdField = Field(...)
    new_order: int = Field(..., gte=0)
