import db
from db.models import Categories, add_update_at_to_update, Actions, Resources
from helpers.types import UpdateResults, RequestWithFullUser
from typing import Union, Optional
from bson import ObjectId
from helpers.secuirty import permissions
from pymongo.errors import DuplicateKeyError


def _update_category(
    filters: dict, update: Union[dict, list[dict]], **kwargs
) -> UpdateResults[Categories]:
    try:
        category = db.CATEGORIES_COLLECTION.find_one_and_update(
            filters, add_update_at_to_update(update), **kwargs
        )
    except DuplicateKeyError:
        return UpdateResults(exists=True)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if category is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=Categories(**category))


def update_category_by_id(
    id: Union[ObjectId, str, Categories],
    name: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
):

    if isinstance(id, Categories):
        id = id.id

    filters = {Categories.Fields.id: ObjectId(id)}

    update = {}

    if name is not None:
        update[Categories.Fields.name_] = name

    if description is not None:
        update[Categories.Fields.description] = description

    return _update_category(filters, {"$set": update}, **kwargs)
