from pydantic import BaseModel, Field
from typing import Any


class FileAttachment(BaseModel):
    filename: str
    content: Any = Field(..., description="Any object that has `read` method")
    mimetype: str
