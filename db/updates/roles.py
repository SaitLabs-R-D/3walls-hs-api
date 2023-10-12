import db
from db.models import (
    add_update_at_to_update,
    Roles,
    Actions,
    Resources,
    RolesInternalNames,
)
from helpers.types import UpdateResults, RequestWithFullUser
from typing import Union, Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from helpers.secuirty import permissions


def _update_role(
    filters: dict, update: Union[dict, list[dict]], **kwargs
) -> UpdateResults[Roles]:
    try:
        user = db.ROLES_COLLECTION.find_one_and_update(
            filters, add_update_at_to_update(update), **kwargs
        )
    except DuplicateKeyError:
        return UpdateResults(exists=True)
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if user is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=Roles(**user))


def update_guest_role(
    categories: Optional[list[Union[ObjectId, str]]] = None,
    lessons: Optional[list[Union[ObjectId, str]]] = None,
):

    update = {}

    if categories is not None:
        update[Roles.Fields.categories] = [ObjectId(c) for c in categories]

    if lessons is not None:
        update[Roles.Fields.lessons] = [ObjectId(l) for l in lessons]

    return _update_role(
        {
            Roles.Fields.internal_name: RolesInternalNames.GUEST,
        },
        {
            "$set": update,
        },
    )
