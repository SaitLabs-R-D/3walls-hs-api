from ..models import SiteHelpCategories, SiteHelp
import db
from helpers.types import InsertResults
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import Optional


def _insert_new_site_help_category(
    category: SiteHelpCategories,
) -> InsertResults[SiteHelpCategories]:
    try:
        res = db.SITE_HELP_CATEGORIES_COLLECTION.insert_one(category.dict(to_db=True))
    except DuplicateKeyError:
        return InsertResults(exists=True, failure=True)
    except:
        return InsertResults(failure=True)

    category.id = res.inserted_id

    return InsertResults(success=True, value=category)


def insert_new_site_help_category(
    name: str,
    description: str,
):

    category = SiteHelpCategories(
        name=name,
        description=description,
    )

    return _insert_new_site_help_category(category)
