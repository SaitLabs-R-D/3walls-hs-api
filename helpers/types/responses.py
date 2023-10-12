from fastapi.responses import JSONResponse, Response
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from io import BytesIO
from .errors import ErrorType


class _Response(JSONResponse):
    def __init__(
        self,
        code: int,
        success: bool,
        data: dict = None,
        message: str = None,
        error_code: ErrorType = None,
        *args,
        **kwargs,
    ):
        self.content = {"success": success}

        if data is not None:
            self.content["content"] = jsonable_encoder(
                data, custom_encoder={ObjectId: str}
            )
        if message is not None:
            self.content["message"] = message

        if error_code is not None:
            self.content["error_code"] = error_code

        kwargs["status_code"] = code

        super().__init__(self.content, *args, **kwargs)


class ApiError(_Response):
    def __init__(self, code: int = 400, error_code: ErrorType = None, *args, **kwargs):
        super().__init__(code, False, error_code=error_code, *args, **kwargs)


class ApiSuccess(_Response):
    def __init__(self, code: int = 200, success: bool = True, *args, **kwargs):
        super().__init__(code, success, *args, **kwargs)


class PaginationResponse(ApiSuccess):
    def __init__(
        self,
        data: list[dict],
        count: int,
        *args,
        **kwargs,
    ):
        super().__init__(
            data={
                "count": count,
                "data": data,
            },
            *args,
            **kwargs,
        )


class ApiRaiseError(ApiError):
    """
    If you can use the ApiError class, use it instead of this class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise HTTPException(
            status_code=self.status_code, detail=self.content, headers=self.headers
        )


class DuplicateDBKeyError(ApiRaiseError):
    def __init__(self, error: DuplicateKeyError, *args, **kwargs):
        super().__init__(
            code=409,
            message=f"entity already exists",
            data={
                "error": "duplicate_key",
                "key": list(error.details["keyValue"].keys()),
            },
            *args,
            **kwargs,
        )


class SendFileResponse(Response):
    def __init__(self, file: BytesIO, filename: str, mime_type: str, *args, **kwargs):
        if kwargs.get("headers"):
            kwargs["headers"][
                "Content-Disposition"
            ] = f"attachment; filename={filename}"
        else:
            kwargs["headers"] = {
                "Content-Disposition": f"attachment; filename={filename}"
            }

        super().__init__(
            content=file.read(),
            media_type=mime_type,
            *args,
            **kwargs,
        )


class BaseResponseModel(BaseModel):
    success: bool = Field(...)
    content: Any = Field(None)
    message: str = Field(None)
    error_code: ErrorType = Field(None)
