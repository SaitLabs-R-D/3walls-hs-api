from typing import Union, Any, Optional
from ..models import SiteHelp, SiteHelpCategories
from bson import ObjectId
from helpers.types import QueryResults, RequestWithPagination
import db
from db import aggregations
from helpers.secuirty import permissions


def _get_site_help(filters: dict[str, Any]) -> QueryResults[SiteHelp]:
    try:
        site_help = db.SITE_HELP_COLLECTION.find_one(filters)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    if site_help is None:
        return QueryResults(not_found=True)

    return QueryResults(value=SiteHelp(**site_help), success=True)


def get_site_help_by_id(site_help_id: Union[ObjectId, str]):
    return _get_site_help({SiteHelp.Fields.id: ObjectId(site_help_id)})


def get_site_helps_for_external(
    category_id: Optional[Union[ObjectId, str]],
    list_view: bool,
    request: RequestWithPagination,
) -> QueryResults[tuple[list[dict], int]]:

    query = {}

    if category_id is not None:
        query[SiteHelp.Fields.category] = ObjectId(category_id)

    pipeline = [
        aggregations.match_query(query),
        aggregations.sort({SiteHelp.Fields.order: 1}),
        aggregations.skip(request.state.offset),
        aggregations.limit(request.state.limit),
    ]

    if list_view:
        pipeline.extend(
            [
                aggregations.lookup(
                    from_=SiteHelpCategories,
                    local_field=SiteHelp.Fields.category,
                    foreign_field=SiteHelpCategories.Fields.id,
                    as_="category",
                ),
                aggregations.unwind("category"),
                aggregations.add_fields(
                    category_name=f"$category.{SiteHelpCategories.Fields.name_}",
                ),
            ]
        )

    pipeline.append(
        aggregations.project(
            [
                SiteHelp.Fields.title_,
                SiteHelp.Fields.description,
                SiteHelp.Fields.background_image,
                SiteHelp.Fields.order,
                "category_name",
            ]
        )
    )

    try:
        cursor = db.SITE_HELP_COLLECTION.aggregate(pipeline)

    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    docs = list(cursor)

    count = len(docs)

    if count < request.state.limit:
        count += request.state.offset
        return QueryResults(value=(docs, count), success=True)
    try:
        count = db.SITE_HELP_COLLECTION.count_documents(query)
    except:
        return QueryResults(failure=True)

    return QueryResults(value=(docs, count), success=True)
