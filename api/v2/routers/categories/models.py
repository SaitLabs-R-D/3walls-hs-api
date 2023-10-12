from pydantic import BaseModel, Field, root_validator
from typing import Union
from fastapi import Query


class CreateCategoryPayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Union[str, None] = Field(None, max_length=200)


class UpdateCategoryPayload(BaseModel):
    name: Union[str, None] = Field(None, min_length=2, max_length=50)
    description: Union[str, None] = Field(None, max_length=200)

    @root_validator
    def check_if_any_field_is_not_none(cls, values):
        if not any([values.get("name"), values.get("description")]):
            raise ValueError("at least one field must be provided")
        return values


class GetCategoriesQueryParams(BaseModel):
    free_text: Union[str, None] = Query(None, max_length=50)
