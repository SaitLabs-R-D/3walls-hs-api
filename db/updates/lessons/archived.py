from ...models import ArchiveLessons, add_update_at_to_update, LessonEdit
import db
from helpers.types import UpdateResults
from typing import Union
from bson import ObjectId


def _update_many_archived_lessons(
    filters: dict, update: Union[list[dict], dict], **kwargs
) -> UpdateResults[int]:

    try:
        res = db.PUBLISHED_LESSONS_COLLECTION.update_many(
            filters, add_update_at_to_update(update), **kwargs
        )
    except:
        return UpdateResults(failure=True)

    if res is None:
        return UpdateResults(not_found=True, failure=True)

    return UpdateResults(success=True, value=res.modified_count)


def change_many_archived_lessons_creator(
    old_creators_ids: Union[ObjectId, str, list[Union[str, ObjectId]]],
    new_creator_id: Union[ObjectId, str],
    **kwargs,
):

    if isinstance(old_creators_ids, list):
        old_creators_ids = [ObjectId(creator_id) for creator_id in old_creators_ids]
    else:
        old_creators_ids = [ObjectId(old_creators_ids)]

    new_creator_id = ObjectId(new_creator_id)

    filters = {
        ArchiveLessons.Fields.creator: {
            "$in": old_creators_ids,
        },
    }

    update = {
        "$set": {
            ArchiveLessons.Fields.creator: new_creator_id,
        }
    }
    return _update_many_archived_lessons(filters, update, **kwargs)


def change_many_editors_of_archived_lessons(
    old_editors_ids: Union[ObjectId, str, list[Union[str, ObjectId]]],
    new_editor_id: Union[ObjectId, str],
    **kwargs,
):

    if isinstance(old_editors_ids, list):
        old_editors_ids = [ObjectId(editor_id) for editor_id in old_editors_ids]
    else:
        old_editors_ids = [ObjectId(old_editors_ids)]

    current_editor_field = (
        f"{ArchiveLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}"
    )

    intial_editor_field = (
        f"{ArchiveLessons.Fields.edit_data}.{LessonEdit.Fields.initial_editor}"
    )

    filters = {
        "$or": [
            {
                current_editor_field: {"$in": old_editors_ids},
            },
            {
                intial_editor_field: {"$in": old_editors_ids},
            },
        ]
    }

    update = [
        {
            "$set": {
                current_editor_field: {
                    "$cond": {
                        "if": {
                            "$in": [
                                f"${current_editor_field}",
                                old_editors_ids,
                            ]
                        },
                        "then": new_editor_id,
                        "else": f"${current_editor_field}",
                    }
                },
                intial_editor_field: {
                    "$cond": {
                        "if": {
                            "$in": [
                                f"${intial_editor_field}",
                                old_editors_ids,
                            ]
                        },
                        "then": new_editor_id,
                        "else": f"${intial_editor_field}",
                    }
                },
            }
        }
    ]

    return _update_many_archived_lessons(filters, update, **kwargs)


def change_many_archived_by_of_archived_lessons(
    old_archived_by_ids: Union[ObjectId, str, list[Union[str, ObjectId]]],
    new_archived_by_id: Union[ObjectId, str],
    **kwargs,
):

    if isinstance(old_archived_by_ids, list):
        old_archived_by_ids = [
            ObjectId(archived_by_id) for archived_by_id in old_archived_by_ids
        ]
    else:
        old_archived_by_ids = [ObjectId(old_archived_by_ids)]

    filters = {
        ArchiveLessons.Fields.archive_by: {"$in": old_archived_by_ids},
    }

    update = {
        "$set": {
            ArchiveLessons.Fields.archive_by: ObjectId(new_archived_by_id),
        }
    }

    return _update_many_archived_lessons(filters, update, **kwargs)
