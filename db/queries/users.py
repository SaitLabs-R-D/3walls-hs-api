from typing import Union, Any, Optional
from ..models import (
    Users,
    Roles,
    DraftLessons,
    Resources,
    Actions,
    PublishedLessons,
    Categories,
    Accounts,
)
from bson import ObjectId
from helpers.types import (
    QueryResults,
    UserPopulateOptions,
    RequestWithPaginationAndFullUser,
    RequestWithFullUser,
)
import db
from db import aggregations
from helpers.secuirty import permissions
from .roles import get_account_manager_role, get_admin_role


def _get_user(
    filters: dict[str, Any], populate: Optional[UserPopulateOptions] = None, **kwargs
) -> QueryResults[Users]:
    try:

        if populate is None:
            user = db.USER_COLLECTION.find_one(filters, **kwargs)
        else:

            pipeline = [
                aggregations.match_query(filters),
                aggregations.limit(1),
            ]

            if populate.role:
                pipeline.extend(aggregations.lookup_user_role())

            if populate.account:
                pipeline.extend(aggregations.lookup_user_account())

            user = db.USER_COLLECTION.aggregate(pipeline)

            user = next(user, None)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    if user is None:
        return QueryResults(not_found=True, failure=True)

    return QueryResults(value=Users(**user), success=True)


def get_user_for_get_me(user_id: Union[str, ObjectId]) -> QueryResults[dict]:

    try:
        user = db.USER_COLLECTION.aggregate(
            [
                aggregations.match_query(
                    {
                        Users.Fields.id: ObjectId(user_id),
                    }
                ),
                aggregations.limit(1),
                *aggregations.lookup_user_role(),
                # aggregations.lookup_user_account(),
                *aggregations.lookup_user_draft_lesson(),
                aggregations.project(
                    [
                        Users.Fields.full_name,
                        Users.Fields.email,
                        f"{Users.Fields.role}.{Roles.Fields.name_}",
                        f"{Users.Fields.role}.{Roles.Fields.id}",
                        f"{Users.Fields.role}.{Roles.Fields.internal_name}",
                    ],
                    draft=f"$draft.{DraftLessons.Fields.id}",
                ),
            ]
        )

        user = next(user, None)

    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    if user is None:
        return QueryResults(not_found=True)

    return QueryResults(value=user, success=True)


def get_user_by_email(email: str, populate: Optional[UserPopulateOptions] = None):
    return _get_user({Users.Fields.email: email}, populate)


def get_user_by_id(
    user_id: Union[str, ObjectId],
    populate: Optional[UserPopulateOptions] = None,
    request: Optional[RequestWithFullUser] = None,
):
    filters = {Users.Fields.id: ObjectId(user_id)}

    if request is not None:
        filters.update(
            permissions.build_filters(
                request,
                Resources.USERS,
                Actions.READ,
            )
        )

    return _get_user(filters, populate)


def get_users_for_external(
    request: RequestWithPaginationAndFullUser,
    role: Optional[Union[str, ObjectId]] = None,
    account: Optional[Union[str, ObjectId]] = None,
) -> QueryResults[tuple[list[dict], int]]:

    default_filters = permissions.build_filters(
        request,
        Resources.USERS,
        Actions.READ_MANY,
    )

    provided_filters = {}

    if role is not None:
        provided_filters[Users.Fields.role] = ObjectId(role)

    if account is not None:
        provided_filters[Users.Fields.account] = ObjectId(account)

    offset = request.state.page * request.state.limit

    try:
        docs = db.USER_COLLECTION.aggregate(
            [
                aggregations.match_query(default_filters),
                aggregations.match_query(provided_filters),
                aggregations.skip(offset),
                aggregations.limit(request.state.limit),
                *aggregations.lookup_user_role(),
                aggregations.project(
                    [
                        Users.Fields.full_name,
                        Users.Fields.email,
                        Users.Fields.phone_number,
                        f"{Users.Fields.role}.{Roles.Fields.name_}",
                        f"{Users.Fields.role}.{Roles.Fields.id}",
                        f"{Users.Fields.role}.{Roles.Fields.internal_name}",
                    ]
                ),
            ]
        )
        docs = list(docs)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    count = len(docs)

    if count < request.state.limit:
        count += offset
        return QueryResults(value=(docs, count), success=True)

    try:
        count = db.USER_COLLECTION.count_documents(
            {
                **provided_filters,
                **default_filters,
            }
        )
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    return QueryResults(value=(docs, count), success=True)


def get_user_by_id_for_external(
    request: RequestWithFullUser,
    user_id: Union[ObjectId, str, Users],
) -> QueryResults[dict]:

    if isinstance(user_id, Users):
        user_id = user_id.id

    filters = {
        Users.Fields.id: ObjectId(user_id),
    }

    filters.update(
        permissions.build_filters(
            request,
            Resources.USERS,
            Actions.READ,
        )
    )

    try:
        doc = db.USER_COLLECTION.aggregate(
            [
                aggregations.match_query(filters),
                aggregations.limit(1),
                aggregations.lookup(
                    from_=Roles,
                    local_field=Users.Fields.role,
                    foreign_field=Roles.Fields.id,
                    as_=Users.Fields.role,
                    pipeline=[
                        aggregations.project(
                            [
                                Roles.Fields.name_,
                                Roles.Fields.internal_name,
                            ]
                        )
                    ],
                ),
                aggregations.unwind(Users.Fields.role),
                aggregations.lookup(
                    from_=Accounts,
                    local_field=Users.Fields.account,
                    foreign_field=Accounts.Fields.id,
                    as_=Users.Fields.account,
                    pipeline=[
                        aggregations.project(
                            [
                                Accounts.Fields.institution_name,
                            ]
                        )
                    ],
                ),
                aggregations.unwind(Users.Fields.account, True),
                aggregations.lookup(
                    from_=PublishedLessons,
                    local_field=Users.Fields.allowed_lessons,
                    foreign_field=PublishedLessons.Fields.id,
                    as_=Users.Fields.allowed_lessons,
                    pipeline=[
                        aggregations.project(
                            [
                                PublishedLessons.Fields.title_,
                            ]
                        )
                    ],
                ),
                aggregations.lookup(
                    from_=Categories,
                    local_field=Users.Fields.allowed_categories,
                    foreign_field=Categories.Fields.id,
                    as_=Users.Fields.allowed_categories,
                    pipeline=[
                        aggregations.project(
                            [
                                Categories.Fields.name_,
                            ]
                        )
                    ],
                ),
                aggregations.unset(
                    Users.Fields.password,
                    Users.Fields.reset_password_token,
                    Users.Fields.registration_token,
                ),
            ]
        )
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    doc = next(doc, None)

    if doc is None:
        return QueryResults(not_found=True)

    return QueryResults(value=doc, success=True)


def get_account_manager_user(
    account: Union[str, ObjectId, Accounts],
    **kwargs,
):

    if isinstance(account, Accounts):
        account = account.id

    role = get_account_manager_role()

    if role.failure:
        return QueryResults(failure=True)

    role = role.value.id

    return _get_user(
        {
            Users.Fields.account: ObjectId(account),
            Users.Fields.role: ObjectId(role),
        },
        **kwargs,
    )


def get_system_admin_user(**kwargs):
    role = get_admin_role()

    if role.failure:
        return QueryResults(failure=True)

    role = role.value.id

    return _get_user(
        {
            Users.Fields.role: ObjectId(role),
        },
        **kwargs,
    )


def get_users_ids_by_account_id(
    account_id: Union[str, ObjectId],
    **kwargs,
) -> QueryResults[list[ObjectId]]:
    account_id = ObjectId(account_id)

    try:
        docs = db.USER_COLLECTION.distinct(
            Users.Fields.id,
            {
                Users.Fields.account: account_id,
            },
            **kwargs,
        )
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    return QueryResults(value=docs, success=True)
