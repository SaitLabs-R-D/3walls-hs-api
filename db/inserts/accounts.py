from ..models import Accounts
import db
from helpers.types import InsertResults
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import Optional


def _insert_new_account(account: Accounts) -> InsertResults[Accounts]:

    try:
        res = db.ACCOUNT_COLLECTION.insert_one(account.dict(to_db=True))
    except DuplicateKeyError:
        return InsertResults(exists=True, failure=True)
    except:
        return InsertResults(failure=True)

    account.id = res.inserted_id

    return InsertResults(success=True, value=account)


def insert_new_account(
    institution_name: str,
    city: str,
    contact_man_name: str,
    email: str,
    phone: str,
    allowed_users: int,
    allowed_lessons: Optional[list[ObjectId, str]] = [],
    allowed_categories: Optional[list[ObjectId, str]] = [],
    logo: Optional[str] = None,
):
    if allowed_lessons is None:
        allowed_lessons = []

    if allowed_categories is None:
        allowed_categories = []

    account = Accounts(
        institution_name=institution_name,
        city=city,
        contact_man_name=contact_man_name,
        email=email,
        phone=phone,
        logo=logo,
        allowed_users=allowed_users,
        allowed_lessons=[ObjectId(lesson) for lesson in allowed_lessons],
        allowed_categories=[ObjectId(category) for category in allowed_categories],
    )

    return _insert_new_account(account)
