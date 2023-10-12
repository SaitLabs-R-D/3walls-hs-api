import db.aggregations.common as aggregations
from db.models import Categories, Roles


def lookup_role_categories(pipeline: list[dict] = []) -> dict:
    return aggregations.lookup(
        Categories,
        Roles.Fields.categories,
        Categories.Fields.id,
        Roles.Fields.categories,
        pipeline=pipeline,
    )
