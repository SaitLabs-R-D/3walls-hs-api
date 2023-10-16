from ..models import Users, Roles, Accounts, Actions, Resources
import db
from helpers.types import InsertResults, RequestWithFullUser
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import Union, Optional
from helpers.secuirty import permissions


def _insert_new_user(user: Users) -> InsertResults[Users]:

    try:
        res = db.USER_COLLECTION.insert_one(user.dict(to_db=True))
    except DuplicateKeyError:
        return InsertResults(failure=True, exists=True)
    except:
        return InsertResults(failure=True)

    user.id = res.inserted_id

    return InsertResults(success=True, value=user)


def insert_new_guest_user(
    guest_role: Union[Roles, ObjectId],
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> InsertResults[Users]:

    if isinstance(guest_role, Roles):
        guest_role = guest_role.id

    user = Users(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=guest_role,
        registration_completed=True,
    )

    return _insert_new_user(user)


def insert_new_account_manager_user(
    account_manager_role: Union[Roles, str, ObjectId],
    account: Union[ObjectId, str, Accounts],
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone_number: str,
) -> InsertResults[Users]:

    if isinstance(account_manager_role, Roles):
        account_manager_role = account_manager_role.id

    if isinstance(account, Accounts):
        account = account.id

    user = Users(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=ObjectId(account_manager_role),
        account=ObjectId(account),
        phone_number=phone_number,
    )

    return _insert_new_user(user)


def insert_new_user(
    request: RequestWithFullUser,
    role: Union[Roles, ObjectId, str],
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    phone_number: Optional[str] = None,
    account: Union[ObjectId, str, Accounts] = None,
):

    if isinstance(role, Roles):
        role = role.id

    if isinstance(account, Accounts):
        account = account.id

    user = Users(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=ObjectId(role),
        account=ObjectId(account) if account else None,
        phone_number=phone_number,
    )

    if not permissions.verify_put_values(
        request, Resources.USERS, user.dict(to_db=True), Actions.CREATE_LIMITES
    ):

        return InsertResults(not_valid=True, failure=True)

    return _insert_new_user(user)
