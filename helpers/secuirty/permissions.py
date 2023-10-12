from typing import Any, Literal, Optional
from db.models import Actions, Resources, Permissions, DynamicSources
from db.models.roles import ResourcesFilterOperators
from fastapi import Request
from helpers.types import RequestWithFullUser


def build_filters(
    request: RequestWithFullUser, resource: Resources, action: Actions
) -> Optional[dict[str, Any]]:

    permission: Permissions

    try:
        permission = request.state.permissions[resource]
    except KeyError:
        for p in request.state.user.role.permissions:
            if p.resource == resource:
                permission = p
                break

    if not permission:
        return None

    filters = {}

    or_filters = []
    and_filters = []

    for filter_ in permission.filters:
        if action in filter_.apply_to:
            if filter_.dynamic:
                if filter_.dynamic_source == DynamicSources.CURRENT_USER:
                    value = request.state.user
                    for field in filter_.dynamic_field:
                        value = value[field]
                    filter_.value = value
                else:
                    print(filter_.dynamic_source)
                    raise Exception("Unknown dynamic source")
            if filter_.is_or:
                or_filters.append(
                    {filter_.field: {filter_.operator.value: filter_.value}}
                )
            elif filter_.is_and:
                and_filters.append(
                    {filter_.field: {filter_.operator.value: filter_.value}}
                )
            else:
                filters[filter_.field] = {filter_.operator.value: filter_.value}

    if or_filters:
        filters["$or"] = or_filters
    if and_filters:
        filters["$and"] = and_filters

    return filters


def verify_put_values(
    request: Request,
    resource: Resources,
    values: dict[str, Any],
    action: Literal[Actions.UPDATE_LIMITES, Actions.CREATE_LIMITES],
) -> bool:

    permission: Permissions

    try:
        permission = request.state.permissions[resource]
    except KeyError:
        for p in request.state.user.role.permissions:
            if p.resource == resource:
                permission = p
                break

    for filter_ in permission.filters:
        if action in filter_.apply_to and filter_.field in values:

            # when there is a edit limit and a wildcard,
            # that means that the field is not editable
            if filter_.value == "*":
                return False

            if filter_.dynamic:
                if filter_.dynamic_source == DynamicSources.CURRENT_USER:
                    value = request.state.user
                    for field in filter_.dynamic_field:
                        value = value[field]
                    filter_.value = value
                else:
                    raise Exception("Unknown dynamic source")
            match filter_.operator:
                case ResourcesFilterOperators.EQUAL:
                    if not values[filter_.field] == filter_.value:
                        return False
                case ResourcesFilterOperators.NOT_EQUAL:
                    if values[filter_.field] == filter_.value:
                        return False
                case ResourcesFilterOperators.IN:
                    if not values[filter_.field] in filter_.value:
                        return False
                case ResourcesFilterOperators.NOT_IN:
                    if values[filter_.field] in filter_.value:
                        return False
                case _:
                    raise NotImplementedError(
                        f"Operator {filter_.operator} not implemented"
                    )

    return True
