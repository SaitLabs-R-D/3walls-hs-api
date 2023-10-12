import db
from db.models import SiteHelp, add_update_at_to_update, Actions, Resources
from helpers.types import UpdateResults, RequestWithFullUser
from typing import Union, Optional
from bson import ObjectId
from helpers.secuirty import permissions
from pymongo.errors import DuplicateKeyError


def _update_site_help(
    filters: dict, update: Union[dict, list[dict]], **kwargs
) -> UpdateResults[SiteHelp]:
    try:
        site_help = db.SITE_HELP_COLLECTION.find_one_and_update(
            filters, add_update_at_to_update(update), **kwargs
        )
    except DuplicateKeyError:
        return UpdateResults(exists=True)
    except Exception as e:
        return UpdateResults(failure=True)

    if site_help is None:
        return UpdateResults(success=True, not_found=True)

    return UpdateResults(success=True, value=SiteHelp(**site_help))


def update_site_help_by_id(
    id: Union[ObjectId, str, SiteHelp],
    pdf: Optional[str] = None,
    background_image: Optional[str] = None,
    title: Optional[str] = None,
    youtube_link: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[Union[str, ObjectId]] = None,
    order: Optional[int] = None,
    **kwargs
):

    if isinstance(id, SiteHelp):
        id = id.id

    filters = {SiteHelp.Fields.id: ObjectId(id)}

    update = {}

    if pdf is not None:
        update[SiteHelp.Fields.pdf] = pdf

    if background_image is not None:
        update[SiteHelp.Fields.background_image] = background_image

    if title is not None:
        update[SiteHelp.Fields.title_] = title

    if youtube_link is not None:
        update[SiteHelp.Fields.youtube_link] = youtube_link

    if description is not None:
        update[SiteHelp.Fields.description] = description

    if category is not None:
        update[SiteHelp.Fields.category] = ObjectId(category)

    if order is not None:
        update[SiteHelp.Fields.order] = order

    return _update_site_help(filters, {"$set": update}, **kwargs)
