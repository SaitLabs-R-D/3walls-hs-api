from typing import Union, Optional
from bson import ObjectId
from ..models import Accounts, Resources, Actions, Users, PublishedLessons, Categories
from helpers.types import (
    QueryResults,
    RequestWithPaginationAndFullUser,
    AccountPopulateOptions,
    RequestWithFullUser,
)
import db
from db import aggregations
from helpers.secuirty import permissions


def _get_account(
    filters: dict, populate: Optional[AccountPopulateOptions] = None, **kwargs
) -> QueryResults[Accounts]:

    try:
        if not populate:
            doc = db.ACCOUNT_COLLECTION.find_one(filters)
        else:
            pipeline = [aggregations.match_query(filters), aggregations.limit(1)]

            if populate.allowed_lessons:
                pipeline.extend(
                    aggregations.lookup(
                        from_=PublishedLessons,
                        local_field=Accounts.Fields.allowed_lessons,
                        foreign_field=PublishedLessons.Fields.id,
                        as_=Accounts.Fields.allowed_lessons,
                    )
                )

            if populate.allowed_categories:
                pipeline.extend(
                    aggregations.lookup(
                        from_=Categories,
                        local_field=Accounts.Fields.allowed_categories,
                        foreign_field=Categories.Fields.id,
                        as_=Accounts.Fields.allowed_categories,
                    )
                )

            doc = db.ACCOUNT_COLLECTION.aggregate(pipeline)

            doc = next(doc, None)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    if doc is None:
        return QueryResults(not_found=True)

    return QueryResults(value=Accounts(**doc), success=True)


def check_account_user_limit(
    account_id: Union[ObjectId, str, Accounts]
) -> QueryResults[bool]:

    if isinstance(account_id, Accounts):
        account_id = account_id.id

    try:
        docs = db.ACCOUNT_COLLECTION.aggregate(
            [
                aggregations.match_query({Accounts.Fields.id: ObjectId(account_id)}),
                aggregations.lookup(
                    from_=Users,
                    local_field=Accounts.Fields.id,
                    foreign_field=Users.Fields.account,
                    as_="users",
                    pipeline=[aggregations.project([])],
                ),
                aggregations.project(
                    [],
                    limit_reached={
                        "$gte": [
                            {"$size": "$users"},
                            f"${Accounts.Fields.allowed_users}",
                        ]
                    },
                ),
            ]
        )

        return QueryResults(value=next(docs)["limit_reached"])
    except Exception as e:
        return QueryResults(failure=True)


def get_accounts_for_external(
    request: RequestWithPaginationAndFullUser,
) -> QueryResults[tuple[list[dict], int]]:

    default_filters = permissions.build_filters(
        request,
        Resources.ACCOUNTS,
        Actions.READ_MANY,
    )

    provided_filters = {}

    offset = request.state.page * request.state.limit

    try:
        docs = db.ACCOUNT_COLLECTION.aggregate(
            [
                aggregations.match_query(default_filters),
                aggregations.match_query(provided_filters),
                aggregations.skip(offset),
                aggregations.limit(request.state.limit),
                aggregations.project(
                    [
                        Accounts.Fields.institution_name,
                        Accounts.Fields.contact_man_name,
                        Accounts.Fields.email,
                        Accounts.Fields.phone,
                        Accounts.Fields.allowed_users,
                        Accounts.Fields.current_users,
                    ]
                ),
            ]
        )
        docs = list(docs)
    except:
        return QueryResults(failure=True)

    count = len(docs)

    if count < request.state.limit:
        count += offset
        return QueryResults(value=(docs, count), success=True)

    try:
        count = db.ACCOUNT_COLLECTION.count_documents(
            {
                **provided_filters,
                **default_filters,
            }
        )
    except:
        return QueryResults(failure=True)

    return QueryResults(value=(docs, count), success=True)


def get_account_by_id_for_external(
    request: RequestWithPaginationAndFullUser,
    account_id: Union[ObjectId, str, Accounts],
) -> QueryResults[dict]:

    if isinstance(account_id, Accounts):
        account_id = account_id.id

    provided_filters = {
        Accounts.Fields.id: ObjectId(account_id),
    }

    default_filters = permissions.build_filters(
        request,
        Resources.ACCOUNTS,
        Actions.READ,
    )

    try:
        docs = db.ACCOUNT_COLLECTION.aggregate(
            [
                aggregations.match_query(default_filters),
                aggregations.match_query(provided_filters),
                aggregations.lookup(
                    from_=PublishedLessons,
                    local_field=Accounts.Fields.allowed_lessons,
                    foreign_field=PublishedLessons.Fields.id,
                    as_=Accounts.Fields.allowed_lessons,
                    pipeline=[aggregations.project([PublishedLessons.Fields.title_])],
                ),
                aggregations.lookup(
                    from_=Categories,
                    local_field=Accounts.Fields.allowed_categories,
                    foreign_field=Categories.Fields.id,
                    as_=Accounts.Fields.allowed_categories,
                    pipeline=[aggregations.project([Categories.Fields.name_])],
                ),
            ]
        )
    except:
        return QueryResults(failure=True)

    try:
        doc = next(docs)
    except StopIteration:
        return QueryResults(not_found=True, failure=True)

    return QueryResults(value=doc, success=True)


def get_account_by_id(
    account_id: Union[ObjectId, str, Accounts],
    request: Optional[RequestWithFullUser] = None,
    populate: Optional[AccountPopulateOptions] = None,
) -> QueryResults[Accounts]:

    if isinstance(account_id, Accounts):
        account_id = account_id.id

    filters = {
        Accounts.Fields.id: ObjectId(account_id),
    }

    if request:
        filters.update(
            permissions.build_filters(
                request,
                Resources.ACCOUNTS,
                Actions.READ,
            )
        )

    return _get_account(
        filters=filters,
        populate=populate,
    )
