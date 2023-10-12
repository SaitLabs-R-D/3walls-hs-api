from fastapi import APIRouter, Depends
from ...middleware import (
    login_required,
)
from . import models
from helpers.types import responses
from helpers import cookies


router = APIRouter(dependencies=[Depends(login_required)])


@router.delete("")
def logout():
    res = responses.ApiSuccess()

    cookies.remove_user_access_token(res)

    return res
