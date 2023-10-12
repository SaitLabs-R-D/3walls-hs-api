from ..models import Categories
import db
from helpers.types import InsertResults
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import Optional


def _insert_new_category(category: Categories) -> InsertResults[Categories]:
    try:
        res = db.CATEGORIES_COLLECTION.insert_one(category.dict(to_db=True))
    except DuplicateKeyError:
        return InsertResults(exists=True, failure=True)
    except:
        return InsertResults(failure=True)

    category.id = res.inserted_id

    return InsertResults(success=True, value=category)


def insert_new_category(
    name: str,
    description: str,
):

    category = Categories(
        name=name,
        description=description,
    )

    return _insert_new_category(category)
