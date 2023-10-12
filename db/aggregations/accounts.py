import db.aggregations.common as aggregations
from db.models import Categories, PublishedLessons, Accounts


def lookup_account_allowed_lessons(pipeline: list[dict] = []) -> dict:

    return aggregations.lookup(
        from_=PublishedLessons,
        local_field=Accounts.Fields.allowed_lessons,
        foreign_field=PublishedLessons.Fields.id,
        as_=Accounts.Fields.allowed_lessons,
        pipeline=pipeline,
    )


def lookup_account_allowed_categories(pipeline: list[dict] = []) -> dict:

    return aggregations.lookup(
        from_=Categories,
        local_field=Accounts.Fields.allowed_categories,
        foreign_field=Categories.Fields.id,
        as_=Accounts.Fields.allowed_categories,
        pipeline=pipeline,
    )
