import db.aggregations.common as aggregations
from db.models import LessonsReviews, Users, PublishedLessons


def lookup_lesson_review_user(pipeline: list[dict] = []) -> list[dict]:
    return [
        aggregations.lookup(
            from_=Users,
            local_field=LessonsReviews.Fields.user,
            foreign_field=Users.Fields.id,
            as_=LessonsReviews.Fields.user,
            pipeline=pipeline,
        ),
        aggregations.unwind(LessonsReviews.Fields.user, True),
    ]


def lookup_lesson_review_lesson(pipeline: list[dict] = []) -> list[dict]:
    return [
        aggregations.lookup(
            from_=PublishedLessons,
            local_field=LessonsReviews.Fields.lesson,
            foreign_field=PublishedLessons.Fields.id,
            as_=LessonsReviews.Fields.lesson,
            pipeline=pipeline,
        ),
        aggregations.unwind(LessonsReviews.Fields.lesson, True),
    ]
