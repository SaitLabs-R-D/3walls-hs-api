from ...models import (
    PublishedLessons,
    add_update_at_to_update,
    LessonEdit,
    Users,
    Actions,
    Resources,
    LessonPart,
)
import db
from helpers.types import UpdateResults, RequestWithFullUser
from typing import Union, Optional
from bson import ObjectId
from helpers.secuirty import permissions


def _update_published_lessons(
    filters: dict, update: Union[list[dict], dict], **kwargs
) -> UpdateResults[PublishedLessons]:
    try:
        res = db.PUBLISHED_LESSONS_COLLECTION.find_one_and_update(
            filters, add_update_at_to_update(update), **kwargs
        )
    except Exception as e:
        print(e)
        return UpdateResults(failure=True)

    if res is None:
        return UpdateResults(not_found=True, failure=True)

    return UpdateResults(success=True, value=PublishedLessons(**res))


def _update_many_published_lessons(
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


def change_many_published_lessons_creator(
    old_creators_ids: Union[ObjectId, str, list[Union[str, ObjectId]]],
    new_creator_id: Union[ObjectId, str],
    **kwargs,
):
    if isinstance(old_creators_ids, list):
        old_creators_ids = [ObjectId(id) for id in old_creators_ids]
    else:
        old_creators_ids = ObjectId(old_creators_ids)
    filters = {
        PublishedLessons.Fields.creator: old_creators_ids,
    }

    update = {
        "$set": {
            PublishedLessons.Fields.creator: ObjectId(new_creator_id),
        }
    }

    return _update_many_published_lessons(filters, update, **kwargs)


def change_many_editors_of_published_lessons(
    old_editors_ids: Union[ObjectId, str, list[Union[str, ObjectId]]],
    new_editor_id: Union[ObjectId, str],
    **kwargs,
):
    current_editor_field = (
        f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}"
    )

    intial_editor_field = (
        f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.initial_editor}"
    )

    if isinstance(old_editors_ids, list):
        old_editors_ids = [ObjectId(id) for id in old_editors_ids]
    else:
        old_editors_ids = [ObjectId(old_editors_ids)]

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

    return _update_many_published_lessons(filters, update, **kwargs)


def change_current_editor_of_published_lesson(
    lesson: Union[ObjectId, str, PublishedLessons],
    new_editor: Union[ObjectId, str, Users],
    # Incase the editor changed between the time the lesson was fetched and the time we are trying to update it
    old_editor: Optional[Union[ObjectId, str, Users]] = None,
    **kwargs,
):
    if isinstance(new_editor, Users):
        new_editor = new_editor.id

    filters = {
        PublishedLessons.Fields.id: ObjectId(lesson),
    }

    if old_editor is not None:
        if isinstance(old_editor, Users):
            old_editor = old_editor.id
        filters[
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}"
        ] = ObjectId(old_editor)

    update = {
        "$set": {
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}": ObjectId(
                new_editor
            )
        }
    }

    return _update_published_lessons(filters, update, **kwargs)


def start_editing_published_lesson(
    lesson: PublishedLessons,
    editor: Union[ObjectId, str, Users],
    **kwargs,
):
    if isinstance(editor, Users):
        editor = editor.id

    filters = {
        PublishedLessons.Fields.id: ObjectId(lesson.id),
    }

    edit_data = LessonEdit(
        initial_editor=ObjectId(editor),
        current_editor=ObjectId(editor),
        parts=lesson.parts,
        categories=lesson.categories,
    )

    update = {
        "$set": {
            PublishedLessons.Fields.edit_data: edit_data.dict(),
            PublishedLessons.Fields.mid_edit: True,
        }
    }

    return _update_published_lessons(filters, update, **kwargs)


def update_published_lesson_base_edit_data(
    lesson: Union[PublishedLessons, ObjectId, str],
    request: RequestWithFullUser,
    title: Optional[str] = None,
    description: Optional[str] = None,
    description_file: Optional[str] = None,
    categories: Optional[list[ObjectId]] = None,
    thumbnail: Optional[str] = None,
    credit: Optional[str] = None,
    **kwargs,
):
    if isinstance(lesson, PublishedLessons):
        lesson = lesson.id

    filters = {
        PublishedLessons.Fields.id: ObjectId(lesson),
    }

    filters.update(
        permissions.build_filters(
            request,
            Resources.PUBLISHED_LESSONS,
            Actions.UPDATE,
        )
    )

    update = {}

    edit_data_field = PublishedLessons.Fields.edit_data

    if title is not None:
        update[f"{edit_data_field}.{LessonEdit.Fields.title_}"] = title

    if description is not None:
        update[f"{edit_data_field}.{LessonEdit.Fields.description}"] = description

    if description_file is not None:
        update[
            f"{edit_data_field}.{LessonEdit.Fields.description_file}"
        ] = description_file

    if categories is not None:
        update[f"{edit_data_field}.{LessonEdit.Fields.categories}"] = [
            ObjectId(category) for category in categories
        ]

    if thumbnail is not None:
        update[f"{edit_data_field}.{LessonEdit.Fields.thumbnail}"] = thumbnail

    if credit is not None:
        update[f"{edit_data_field}.{LessonEdit.Fields.credit}"] = credit

    return _update_published_lessons(filters, {"$set": update}, **kwargs)


def add_part_to_published_lesson(
    lesson: PublishedLessons, new_part_order: int, part_type: LessonPart.Types
):
    filters = {
        PublishedLessons.Fields.id: ObjectId(lesson.id),
        PublishedLessons.Fields.mid_edit: True,
    }

    new_part = LessonPart(
        order=new_part_order,
        type=part_type,
    )

    lesson.edit_data.parts.append(new_part)

    update = {
        "$set": {
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}": [
                part.dict() for part in lesson.edit_data.parts
            ],
        }
    }

    return _update_published_lessons(filters, update, return_document=True)


def reorder_parts_in_published_lesson(
    lesson_id: Union[ObjectId, str],
    request: RequestWithFullUser,
    parts: dict[str, int],
):
    parts_ids = list(parts.keys())

    new_order = list(parts.values())

    filters = permissions.build_filters(
        request,
        Resources.PUBLISHED_LESSONS,
        Actions.UPDATE,
    )

    filters.update(
        {
            PublishedLessons.Fields.id: ObjectId(lesson_id),
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}": {
                "$size": len(set(parts_ids)),
                "$all": [{"$elemMatch": {LessonPart.Fields.id: {"$in": parts_ids}}}],
            },
        }
    )

    update = [
        {
            "$set": {
                f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}": {
                    "$map": {
                        "input": f"${PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}",
                        "in": {
                            "$mergeObjects": [
                                "$$this",
                                {
                                    LessonPart.Fields.order: {
                                        "$arrayElemAt": [
                                            new_order,
                                            {
                                                "$indexOfArray": [
                                                    parts_ids,
                                                    f"$$this.{LessonPart.Fields.id}",
                                                ]
                                            },
                                        ],
                                    },
                                },
                            ]
                        },
                    }
                }
            }
        }
    ]

    return _update_published_lessons(filters, update, return_document=True)


def update_part_title_in_published_lesson(
    lesson_id: Union[ObjectId, str],
    part_id: str,
    title: str,
    request: RequestWithFullUser,
):
    filters = permissions.build_filters(
        request,
        Resources.PUBLISHED_LESSONS,
        Actions.UPDATE,
    )

    filters.update(
        {
            PublishedLessons.Fields.id: ObjectId(lesson_id),
            PublishedLessons.Fields.mid_edit: True,
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}.{LessonPart.Fields.id}": part_id,
        }
    )

    update = {
        "$set": {
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}.$.{LessonPart.Fields.title_}": title,
        }
    }

    return _update_published_lessons(
        filters,
        update,
        return_document=True,
    )


def return_edit_to_initial_editor(
    lesson_id: Union[ObjectId, str],
    request: RequestWithFullUser,
):
    filters = permissions.build_filters(
        request,
        Resources.PUBLISHED_LESSONS,
        Actions.UPDATE,
    )

    filters.update(
        {
            PublishedLessons.Fields.id: ObjectId(lesson_id),
            PublishedLessons.Fields.mid_edit: True,
        }
    )

    update = [
        {
            "$set": {
                f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}": f"${PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.initial_editor}",
            }
        }
    ]

    return _update_published_lessons(filters, update, return_document=True)


def add_view_to_published_lesson(lesson_id: Union[ObjectId, str], views: int = 1):
    filters = {
        PublishedLessons.Fields.id: ObjectId(lesson_id),
    }

    update = {
        "$inc": {
            PublishedLessons.Fields.viewed: views,
        }
    }

    return _update_published_lessons(filters, update, return_document=True)


def update_lesson_part_panoramic(
    lesson: Union[PublishedLessons, ObjectId, str],
    request: RequestWithFullUser,
    part_id: str,
    file_path: Optional[str] = None,
    panoramic_url: Optional[str] = None,
    **kwargs,
):
    if isinstance(lesson, PublishedLessons):
        lesson = lesson.id

    filters = {
        PublishedLessons.Fields.id: ObjectId(lesson),
    }

    filters.update(
        permissions.build_filters(
            request,
            Resources.PUBLISHED_LESSONS,
            Actions.UPDATE,
        )
    )

    filters[
        f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}.{LessonPart.Fields.id}"
    ] = part_id

    update_set = {}

    if file_path is not None:
        if not file_path:
            file_path = None
        update_set[
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}.$.{LessonPart.Fields.gcp_path}"
        ] = file_path

    if panoramic_url is not None:
        if not panoramic_url:
            panoramic_url = None
        update_set[
            f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.parts}.$.{LessonPart.Fields.panoramic_url}"
        ] = panoramic_url

    update = {
        "$set": update_set,
    }

    return _update_published_lessons(filters, update, **kwargs)
