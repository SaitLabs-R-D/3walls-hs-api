from typing import Any, Union, Optional
from ..models import (
    Roles,
    RolesInternalNames,
    Actions,
    Resources,
    Categories,
    PublishedLessons,
)
from helpers.types import QueryResults, RequestWithFullUser
import db
from functools import cache
from bson import ObjectId
from helpers.secuirty import permissions
from db import aggregations


def _get_role(filters: dict[str, Any]) -> QueryResults[Roles]:
    try:
        role = db.ROLES_COLLECTION.find_one(filters)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    if role is None:
        return QueryResults(not_found=True)

    return QueryResults(value=Roles(**role), success=True)


@cache
def get_role_cache(internal_name: str) -> QueryResults[Roles]:
    return _get_role({Roles.Fields.internal_name: internal_name})


def get_guest_role(from_cache: bool = True):
    if from_cache:
        return get_role_cache(RolesInternalNames.GUEST)

    return _get_role({Roles.Fields.internal_name: RolesInternalNames.GUEST})


def get_account_manager_role(from_cache: bool = True):

    if from_cache:
        return get_role_cache(RolesInternalNames.INSTATUTION_MANAGER)

    return _get_role(
        {Roles.Fields.internal_name: RolesInternalNames.INSTATUTION_MANAGER}
    )


def get_admin_role(from_cache: bool = True):

    if from_cache:
        return get_role_cache(RolesInternalNames.ADMIN)

    return _get_role({Roles.Fields.internal_name: RolesInternalNames.ADMIN})


def get_role_by_id(
    role_id: Union[ObjectId, str],
    request: Optional[RequestWithFullUser] = None,
):

    filters = {Roles.Fields.id: ObjectId(role_id)}

    if request is not None:
        filters.update(
            permissions.build_filters(
                request,
                Resources.ROLES,
                Actions.READ,
            )
        )

    return _get_role(filters)


def get_roles_for_external(
    request: RequestWithFullUser,
    accountable: bool = False,
    not_accountable: bool = False,
) -> QueryResults[list[dict]]:

    filters = permissions.build_filters(
        request,
        Resources.ROLES,
        Actions.READ,
    )

    if accountable:
        filters.update({Roles.Fields.require_account: True})

    if not_accountable:
        filters.update({Roles.Fields.require_account: False})

    try:
        roles = db.ROLES_COLLECTION.find(
            filters, {Roles.Fields.id: 1, Roles.Fields.name_: 1}
        )
    except:
        return QueryResults(failure=True)

    return QueryResults(value=list(roles), success=True)


def get_guest_role_full_extarnel(
    request: RequestWithFullUser,
) -> QueryResults[dict]:

    default_filters = permissions.build_filters(
        request=request,
        resource=Resources.ROLES,
        action=Actions.READ,
    )

    if default_filters is None:
        return QueryResults(failure=True)

    pipeline = [
        aggregations.match_query(default_filters),
        aggregations.match_query(
            {Roles.Fields.internal_name: RolesInternalNames.GUEST}
        ),
        aggregations.lookup(
            from_=Categories,
            local_field=Roles.Fields.categories,
            foreign_field=Categories.Fields.id,
            as_=Roles.Fields.categories,
            pipeline=[aggregations.project([Categories.Fields.name_])],
        ),
        aggregations.lookup(
            from_=PublishedLessons,
            local_field=Roles.Fields.lessons,
            foreign_field=PublishedLessons.Fields.id,
            as_=Roles.Fields.lessons,
            pipeline=[aggregations.project([PublishedLessons.Fields.title_])],
        ),
        aggregations.project(
            [
                Roles.Fields.categories,
                Roles.Fields.name_,
                Roles.Fields.internal_name,
                Roles.Fields.lessons,
            ]
        ),
    ]

    try:
        cursor = db.ROLES_COLLECTION.aggregate(pipeline)
    except:
        return QueryResults(failure=True)

    role = next(cursor, None)

    if role is None:
        return QueryResults(not_found=True)

    return QueryResults(value=role, success=True)
