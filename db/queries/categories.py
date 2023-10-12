from typing import Union, Any
from ..models import Categories, Resources, Actions, PublishedLessons
from bson import ObjectId
from helpers.types import QueryResults, RequestWithPaginationAndFullUser
import db
from db import aggregations
from helpers.secuirty import permissions


def _get_category(filters: dict[str, Any]) -> QueryResults[Categories]:
    try:
        category = db.CATEGORIES_COLLECTION.find_one(filters)
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    if category is None:
        return QueryResults(not_found=True)

    return QueryResults(value=Categories(**category), success=True)


def get_category_by_id(category_id: Union[ObjectId, str]):
    return _get_category({Categories.Fields.id: ObjectId(category_id)})


def validate_categories_exists(
    category_ids: list[Union[ObjectId, str]]
) -> QueryResults[None]:
    try:
        categories = db.CATEGORIES_COLLECTION.count_documents(
            {
                Categories.Fields.id: {
                    "$in": [ObjectId(category_id) for category_id in category_ids]
                }
            }
        )
    except:
        return QueryResults(failure=True)

    if not categories == len(category_ids):
        return QueryResults(not_found=True)

    return QueryResults(success=True)


def get_categories_for_external(
    free_text: str,
    request: RequestWithPaginationAndFullUser,
) -> QueryResults[tuple[list[dict], int]]:

    query = {}

    if free_text:
        query = {Categories.Fields.name_: {"$regex": free_text, "$options": "i"}}

    try:
        docs = list(
            db.CATEGORIES_COLLECTION.find(
                query,
                projection={
                    Categories.Fields.name_: 1,
                    Categories.Fields.description: 1,
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
        count = db.CATEGORIES_COLLECTION.count_documents(query)
    except:
        return QueryResults(failure=True)

    return QueryResults(value=(docs, count), success=True)


def get_categories_associated_with_user(
    free_text: str,
    request: RequestWithPaginationAndFullUser,
) -> QueryResults[tuple[list[dict], int]]:

    default_filters = permissions.build_filters(
        request,
        Resources.PUBLISHED_LESSONS,
        Actions.READ_MANY,
    )

    base_pipeline = [
        aggregations.match_query(default_filters),
        aggregations.unwind(PublishedLessons.Fields.categories),
        aggregations.group(
            {
                Categories.Fields.id: f"${PublishedLessons.Fields.categories}",
            }
        ),
        aggregations.lookup(
            from_=Categories,
            local_field=Categories.Fields.id,
            foreign_field=Categories.Fields.id,
            as_="category",
        ),
        aggregations.unwind("category"),
        aggregations.replace_root("category"),
    ]

    if free_text:
        base_pipeline.append(
            aggregations.match_query(
                {
                    Categories.Fields.name_: {
                        "$regex": f".*{free_text}.*",
                    }
                }
            ),
        )

    try:
        docs = list(
            db.PUBLISHED_LESSONS_COLLECTION.aggregate(
                [
                    *base_pipeline,
                    aggregations.skip(request.state.offset),
                    aggregations.limit(request.state.limit),
                ]
            )
        )
    except Exception as e:
        print(e)
        return QueryResults(failure=True)

    count = len(docs)

    if count < request.state.limit:
        count += request.state.offset
        return QueryResults(value=(docs, count), success=True)

    try:
        count = db.PUBLISHED_LESSONS_COLLECTION.aggregate(
            [
                *base_pipeline,
                aggregations.count("count"),
            ]
        )[0]["count"]
    except:
        return QueryResults(failure=True)

    return QueryResults(value=(docs, count), success=True)


def validate_many_categories_exists(
    ids: list[Union[ObjectId, str]],
) -> QueryResults[bool]:
    try:
        categories = db.CATEGORIES_COLLECTION.count_documents(
            {"_id": {"$in": [ObjectId(id) for id in ids]}}
        )
    except:
        return QueryResults(failure=True)

    return QueryResults(success=True, value=categories == len(ids))
