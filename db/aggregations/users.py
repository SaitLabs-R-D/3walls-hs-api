import db.aggregations.common as aggregations
from functools import cache
from db.models import Users, Roles, Accounts, DraftLessons


def lookup_user_role(
    pipeline: list[dict] = [],
) -> list[dict]:
    return [
        aggregations.lookup(
            Roles,
            Users.Fields.role,
            Roles.Fields.id,
            Users.Fields.role,
            pipeline=pipeline,
        ),
        aggregations.unwind(Users.Fields.role),
    ]


def lookup_user_account(
    pipeline: list[dict] = [],
) -> list[dict]:
    return [
        aggregations.lookup(
            Accounts,
            Users.Fields.account,
            Accounts.Fields.id,
            Users.Fields.account,
            pipeline=pipeline,
        ),
        # some users don't have an account
        aggregations.unwind(Users.Fields.account, True),
    ]


@cache
def lookup_user_draft_lesson() -> list[dict]:
    """
    The draft will be in the "draft" field.
    """
    return [
        aggregations.lookup(
            DraftLessons,
            Users.Fields.id,
            DraftLessons.Fields.creator,
            "draft",
        ),
        # some users don't have a draft lesson
        aggregations.unwind("draft", True),
    ]
