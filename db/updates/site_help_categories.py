import db
from db.models import SiteHelpCategories, add_update_at_to_update, Actions, Resources
from helpers.types import UpdateResults, RequestWithFullUser
from typing import Union, Optional
from bson import ObjectId
from helpers.secuirty import permissions
from pymongo.errors import DuplicateKeyError


def _update_site_help_category(
    filters: dict, update: Union[dict, list[dict]], **kwargs
) -> UpdateResults[SiteHelpCategories]:
    try:
        category = db.SITE_HELP_CATEGORIES_COLLECTION.find_one_and_update(
            filters, add_update_at_to_update(update), **kwargs
        )
    except DuplicateKeyError:
        return UpdateResults(exists=True)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if category is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=SiteHelpCategories(**category))


def update_site_help_category_by_id(
    id: Union[ObjectId, str, SiteHelpCategories],
    name: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
):

    if isinstance(id, SiteHelpCategories):
        id = id.id

    filters = {SiteHelpCategories.Fields.id: ObjectId(id)}

    update = {}

    if name is not None:
        update[SiteHelpCategories.Fields.name_] = name

    if description is not None:
        update[SiteHelpCategories.Fields.description] = description

    return _update_site_help_category(filters, {"$set": update}, **kwargs)
