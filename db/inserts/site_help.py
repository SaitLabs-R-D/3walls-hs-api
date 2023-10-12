from ..models import SiteHelpCategories, SiteHelp
import db
from helpers.types import InsertResults
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import Optional


def _insert_new_site_help(site_help: SiteHelp, **kwargs) -> InsertResults[SiteHelp]:
    try:
        res = db.SITE_HELP_COLLECTION.insert_one(site_help.dict(to_db=True), **kwargs)
    except DuplicateKeyError:
        return InsertResults(exists=True, failure=True)
    except:
        return InsertResults(failure=True)

    site_help.id = res.inserted_id

    return InsertResults(success=True, value=site_help)
