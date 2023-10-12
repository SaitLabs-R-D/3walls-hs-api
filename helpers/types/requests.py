from fastapi import Request
from db.models import (
    DraftLessons,
    Users,
    Actions,
    Resources,
    Permissions,
    DynamicSources,
)
from db.models.roles import ResourcesFilterOperators
from typing import Any, Literal


class RequestWithUserId(Request):
    class State:
        user_id: str

    @property
    def state(self) -> State:
        return super().state


class RequestWithDraft(Request):
    class State:
        draft: DraftLessons
        user_id: str

    @property
    def state(self) -> State:
        return super().state


class RequestWithFullUser(Request):
    """
    Use this class only after the check_user_permission middleware
    """

    class State:
        user_id: str
        user: Users

    @property
    def state(self) -> State:
        return super().state


class RequestWithPaginationAndFullUser(RequestWithFullUser):
    class State:
        user_id: str
        user: Users
        page: int
        limit: int
        offset: int

    @property
    def state(self) -> State:
        return super().state


class RequestWithPagination(Request):
    class State:
        user_id: str
        page: int
        limit: int
        offset: int

    @property
    def state(self) -> State:
        return super().state
