import db
from db.models import Accounts, add_update_at_to_update, Actions, Resources
from helpers.types import UpdateResults, RequestWithFullUser
from typing import Union, Optional
from bson import ObjectId
from helpers.secuirty import permissions
from pymongo.errors import DuplicateKeyError


def _update_account(
    filters: dict, update: Union[dict, list[dict]], **kwargs
) -> UpdateResults[Accounts]:
    try:
        user = db.ACCOUNT_COLLECTION.find_one_and_update(
            filters, add_update_at_to_update(update), **kwargs
        )
    except DuplicateKeyError:
        return UpdateResults(exists=True)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if user is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=Accounts(**user))


def _delete_account(filters: dict, **kwargs) -> UpdateResults[Accounts]:
    try:
        account = db.ACCOUNT_COLLECTION.find_one_and_delete(filters, **kwargs)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if account is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=Accounts(**account))


def update_account_by_id(
    account_id: Union[ObjectId, str, Accounts],
    request: Optional[RequestWithFullUser] = None,
    allowed_categories: Optional[list[Union[ObjectId, str]]] = None,
    allowed_lessons: Optional[list[Union[ObjectId, str]]] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    allowed_users: Optional[int] = None,
    logo: Optional[str] = None,
    city: Optional[str] = None,
    institution_name: Optional[str] = None,
    contact_man_name: Optional[str] = None,
):

    if isinstance(account_id, Accounts):
        account_id = account_id.id

    filters = {Accounts.Fields.id: ObjectId(account_id)}

    update = {}

    if institution_name is not None:
        update[Accounts.Fields.institution_name] = institution_name
    if city is not None:
        update[Accounts.Fields.city] = city
    if logo is not None:
        update[Accounts.Fields.logo] = logo
    if allowed_users is not None:
        update[Accounts.Fields.allowed_users] = allowed_users
        # If we are updating the allowed users count, we only allow it to be more than the current users count
        filters[Accounts.Fields.current_users] = {"$lte": allowed_users}
    if email is not None:
        update[Accounts.Fields.email] = email
    if phone is not None:
        update[Accounts.Fields.phone] = phone
    if allowed_categories is not None:
        update[Accounts.Fields.allowed_categories] = [
            ObjectId(cat) for cat in allowed_categories
        ]
    if allowed_lessons is not None:
        update[Accounts.Fields.allowed_lessons] = [
            ObjectId(lesson) for lesson in allowed_lessons
        ]
    if contact_man_name is not None:
        update[Accounts.Fields.contact_man_name] = contact_man_name

    if request:
        if not permissions.verify_put_values(
            request, Resources.ACCOUNTS, update, Actions.UPDATE_LIMITES
        ):
            return UpdateResults(not_valid=True, failure=True)

        filters.update(
            permissions.build_filters(
                request,
                Resources.ACCOUNTS,
                Actions.UPDATE,
            )
        )

    return _update_account(filters, {"$set": update})


def update_account_current_users_count(
    account_id: Union[ObjectId, str],
    # Any number except 0 to increase the count
    current_users_count: int,
    **kwargs,
):

    if current_users_count == 0:
        return UpdateResults(failure=True, not_valid=True)

    return _update_account(
        {Accounts.Fields.id: ObjectId(account_id)},
        {"$inc": {Accounts.Fields.current_users: current_users_count}},
        **kwargs,
    )


def delete_account_by_id(
    account_id: Union[ObjectId, str, Accounts],
    request: Optional[RequestWithFullUser] = None,
    **kwargs,
):

    if isinstance(account_id, Accounts):
        account_id = account_id.id

    filters = {Accounts.Fields.id: ObjectId(account_id)}

    if request:
        filters.update(
            permissions.build_filters(
                request,
                Resources.ACCOUNTS,
                Actions.DELETE,
            )
        )

    return _delete_account(filters, **kwargs)
