from helpers.exceptions.redirect import RedirectException
from db import queries
from db.models import Actions, Resources
from helpers.types import (
    UserPopulateOptions,
    RequestWithUserId,
    Cookeys,
    RediractsPaths,
    responses,
)
from typing import Callable


def check_user_permission(
    needed_resources: dict[Resources, list[Actions]]
) -> Callable[[RequestWithUserId], None]:
    def real_func(request: RequestWithUserId):

        user_res = queries.get_user_by_id(
            user_id=request.state.user_id,
            populate=UserPopulateOptions(role=True, account=True),
        )

        if user_res.failure:
            if user_res.not_found:
                raise RedirectException(
                    RediractsPaths.LOGIN.value,
                    remove_cookies=[Cookeys.ACCESS_TOKEN.value],
                )
            return responses.ApiRaiseError(message="Error while getting user data")

        user = user_res.value

        request.state.user = user

        resources_permissions = [
            permission
            for permission in user.role.permissions
            if permission.resource in needed_resources
        ]

        if not resources_permissions:
            return responses.ApiRaiseError(
                message="You don't have permission to access this page", code=403
            )

        if not len(resources_permissions) == len(needed_resources):
            return responses.ApiRaiseError(
                message="Not enough permissions to access this route", code=403
            )

        request.state.permissions = {}
        for permission in resources_permissions:
            if not all(
                action in permission.actions
                for action in needed_resources[permission.resource]
            ):
                return responses.ApiRaiseError(
                    message="Not enough permissions to access this route", code=403
                )

            request.state.permissions[permission.resource] = permission

    return real_func
