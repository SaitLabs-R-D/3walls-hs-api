import db.aggregations.common as aggregations
from db.models import Categories, Users, ArchiveLessons
from db.models.lessons.common import BaseLessonFields, LessonEdit


def lookup_lesson_categories(pipeline: list[dict] = []) -> dict:
    return aggregations.lookup(
        from_=Categories,
        local_field=BaseLessonFields.categories,
        foreign_field=Categories.Fields.id,
        as_=BaseLessonFields.categories,
        pipeline=pipeline,
    )


def lookup_lesson_creator(pipeline: list[dict] = []) -> list[dict]:
    return [
        aggregations.lookup(
            from_=Users,
            local_field=BaseLessonFields.creator,
            foreign_field=Users.Fields.id,
            as_=BaseLessonFields.creator,
            pipeline=pipeline,
        ),
        aggregations.unwind(BaseLessonFields.creator, True),
    ]


def lookup_lesson_current_editor(pipeline: list[dict] = []) -> list[dict]:

    current_editor_field = (
        f"{BaseLessonFields.edit_data}.{LessonEdit.Fields.current_editor}"
    )

    return [
        aggregations.lookup(
            from_=Users,
            local_field=current_editor_field,
            foreign_field=Users.Fields.id,
            as_=current_editor_field,
            pipeline=pipeline,
        ),
        aggregations.unwind(current_editor_field, True),
    ]


def lookup_lesson_initial_editor(pipeline: list[dict] = []) -> list[dict]:

    initial_editor_field = (
        f"{BaseLessonFields.edit_data}.{LessonEdit.Fields.initial_editor}"
    )

    return [
        aggregations.lookup(
            from_=Users,
            local_field=initial_editor_field,
            foreign_field=Users.Fields.id,
            as_=initial_editor_field,
            pipeline=pipeline,
        ),
        aggregations.unwind(initial_editor_field, True),
    ]


def lookup_lesson_archived_by(pipeline: list[dict] = []) -> list[dict]:

    return [
        aggregations.lookup(
            from_=Users,
            local_field=ArchiveLessons.Fields.archive_by,
            foreign_field=Users.Fields.id,
            as_=ArchiveLessons.Fields.archive_by,
            pipeline=pipeline,
        ),
        aggregations.unwind(ArchiveLessons.Fields.archive_by, True),
    ]
