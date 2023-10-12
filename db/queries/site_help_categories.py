from typing import Union, Any
from ..models import SiteHelpCategories, Resources, Actions, PublishedLessons
from bson import ObjectId
from helpers.types import QueryResults, RequestWithPagination
import db
from db import aggregations
from helpers.secuirty import permissions


def _get_help_category(filters: dict[str, Any]) -> QueryResults[SiteHelpCategories]:
    try:
        category = db.SITE_HELP_CATEGORIES_COLLECTION.find_one(filters)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    if category is None:
        return QueryResults(not_found=True)

    return QueryResults(value=SiteHelpCategories(**category), success=True)


def get_site_help_category_by_id(category_id: Union[ObjectId, str]):
    return _get_help_category({SiteHelpCategories.Fields.id: ObjectId(category_id)})


def get_site_help_categories_for_external(
    request: RequestWithPagination,
) -> QueryResults[tuple[list[dict], int]]:

    query = {}

    try:
        docs = list(
            db.SITE_HELP_CATEGORIES_COLLECTION.find(
                query,
                projection={
                    SiteHelpCategories.Fields.name_: 1,
                    SiteHelpCategories.Fields.description: 1,
                },
            )
            .skip(request.state.offset)
            .limit(request.state.limit)
        )
    except:
        return QueryResults(failure=True)

    count = len(docs)

    if count < request.state.limit:
        count += request.state.offset
        return QueryResults(value=(docs, count), success=True)

    try:
        count = db.SITE_HELP_CATEGORIES_COLLECTION.count_documents(query)
    except:
        return QueryResults(failure=True)

    return QueryResults(value=(docs, count), success=True)
