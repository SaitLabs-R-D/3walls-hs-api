import db
from db.models import Users, add_update_at_to_update, Roles, Actions, Resources
from db.queries import get_guest_role
from helpers.types import UpdateResults, RequestWithFullUser
from typing import Union, Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from helpers.secuirty import permissions


def _update_user(
    filters: dict, update: Union[dict, list[dict]], **kwargs
) -> UpdateResults[Users]:
    try:
        user = db.USER_COLLECTION.find_one_and_update(
            filters, add_update_at_to_update(update), **kwargs
        )
    except DuplicateKeyError:
        return UpdateResults(exists=True)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if user is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=Users(**user))


def _delete_user(filters: dict, **kwargs) -> UpdateResults[Users]:
    try:
        user = db.USER_COLLECTION.find_one_and_delete(filters, **kwargs)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if user is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=Users(**user))


def _delete_many_users(filters: dict, **kwargs) -> UpdateResults[int]:
    try:
        res = db.USER_COLLECTION.delete_many(filters, **kwargs)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    return UpdateResults(success=True, value=res.deleted_count)


def set_user_registration_token(
    user_id: Union[ObjectId, str], token: str
) -> UpdateResults[Users]:
    return _update_user(
        {Users.Fields.id: ObjectId(user_id)},
        {"$set": {Users.Fields.registration_token: token}},
    )


def set_user_registration_completed(
    user_id: Union[ObjectId, str], token: str, password: Optional[str] = None
) -> UpdateResults[Users]:

    update = {
        Users.Fields.registration_token: None,
        Users.Fields.registration_completed: True,
    }

    if password is not None:
        update[Users.Fields.password] = password

    return _update_user(
        {
            Users.Fields.id: ObjectId(user_id),
            Users.Fields.registration_token: token,
            Users.Fields.registration_completed: False,
        },
        {"$set": update},
    )


def update_user_by_id(
    user_id: Union[ObjectId, str],
    request: Optional[RequestWithFullUser] = None,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: Union[Roles, ObjectId, str] = None,
    password: Optional[str] = None,
    allowed_lessons: Optional[list[Union[ObjectId, str]]] = None,
    allowed_categories: Optional[list[Union[ObjectId, str]]] = None,
    phone_number: Optional[str] = None,
    # some updates cannot be made to users with accounts
    # for example, you cannot change the role of a user with an account to certain roles
    account_need_to_be_null: bool = False,
    reset_password_token: Optional[str] = None,
    **kwargs,
) -> UpdateResults[Users]:
    update = {}

    if account_need_to_be_null:
        update[Users.Fields.account] = None

    filters = {Users.Fields.id: ObjectId(user_id)}

    if email is not None:
        if not email.startswith("$"):
            update[Users.Fields.email] = email

    if first_name is not None or last_name is not None:
        if first_name is not None:
            if first_name.startswith("$"):
                first_name = first_name[1:]
            update[Users.Fields.first_name] = first_name

        if last_name is not None:
            if last_name.startswith("$"):
                last_name = last_name[1:]
            update[Users.Fields.last_name] = last_name

        update[Users.Fields.full_name] = {
            "$concat": [
                update.get(Users.Fields.first_name, "$first_name"),
                " ",
                update.get(Users.Fields.last_name, "$last_name"),
            ]
        }

    if role is not None:
        if isinstance(role, Roles):
            role = role.id

        guest_role = get_guest_role()

        if guest_role.failure:
            return UpdateResults(failure=True)

        update[Users.Fields.role] = ObjectId(role)

    if password is not None:
        update[Users.Fields.password] = {"$literal": password}

    if allowed_lessons is not None:
        update[Users.Fields.allowed_lessons] = [
            ObjectId(les) for les in allowed_lessons
        ]

    if allowed_categories is not None:
        update[Users.Fields.allowed_categories] = [
            ObjectId(cat) for cat in allowed_categories
        ]

    if request:
        if not permissions.verify_put_values(
            request, Resources.USERS, update, Actions.UPDATE_LIMITES
        ):
            return UpdateResults(not_valid=True, failure=True)

        filters.update(
            permissions.build_filters(
                request,
                Resources.USERS,
                Actions.UPDATE,
            )
        )

    if phone_number is not None:
        update[Users.Fields.phone_number] = phone_number

    if reset_password_token is not None:
        update[Users.Fields.reset_password_token] = reset_password_token

    return _update_user(filters, [{"$set": update}], **kwargs)


def delete_user_by_id(
    user_id: Union[ObjectId, str],
    request: Optional[RequestWithFullUser] = None,
    **kwargs,
) -> UpdateResults[Users]:
    filters = {Users.Fields.id: ObjectId(user_id)}

    if request:
        filters.update(
            permissions.build_filters(
                request,
                Resources.USERS,
                Actions.DELETE,
            )
        )

    return _delete_user(filters, **kwargs)


def delete_many_users_by_ids(
    user_ids: list[Union[ObjectId, str]],
    request: Optional[RequestWithFullUser] = None,
    **kwargs,
) -> UpdateResults[int]:
    filters = {Users.Fields.id: {"$in": [ObjectId(id) for id in user_ids]}}

    if request:
        filters.update(
            permissions.build_filters(
                request,
                Resources.USERS,
                Actions.DELETE,
            )
        )

    return _delete_many_users(filters, **kwargs)


def change_user_password_with_token(
    user_id: Union[ObjectId, str],
    token: str,
    # hashed password
    password: str,
) -> UpdateResults[Users]:
    return _update_user(
        {
            Users.Fields.id: ObjectId(user_id),
            Users.Fields.reset_password_token: token,
        },
        {
            "$set": {
                Users.Fields.password: password,
                Users.Fields.reset_password_token: None,
            }
        },
    )
