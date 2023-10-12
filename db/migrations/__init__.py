from db.models import DraftLessons, PublishedLessons, ArchiveLessons, LessonPart
import db


def add_lesson_part_type_and_gcp_path_for_draft_lessons():
    db.DRAFT_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{DraftLessons.Fields.parts}.$[part].{LessonPart.Fields.type_}": LessonPart.Types.NORMAL.value,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.type_}": {"$exists": False}}],
    )

    db.DRAFT_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{DraftLessons.Fields.parts}.$[part].{LessonPart.Fields.gcp_path}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.gcp_path}": {"$exists": False}}],
    )

    db.DRAFT_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{DraftLessons.Fields.parts}.$[part].{LessonPart.Fields.panoramic_url}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.panoramic_url}": {"$exists": False}}],
    )


def add_lesson_part_type_and_gcp_path_for_published_lessons():
    db.PUBLISHED_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{PublishedLessons.Fields.parts}.$[part].{LessonPart.Fields.type_}": LessonPart.Types.NORMAL.value,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.type_}": {"$exists": False}}],
    )

    db.PUBLISHED_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{PublishedLessons.Fields.parts}.$[part].{LessonPart.Fields.gcp_path}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.gcp_path}": {"$exists": False}}],
    )

    db.PUBLISHED_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{PublishedLessons.Fields.parts}.$[part].{LessonPart.Fields.panoramic_url}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.panoramic_url}": {"$exists": False}}],
    )

    db.PUBLISHED_LESSONS_COLLECTION.update_many(
        {
            f"{PublishedLessons.Fields.parts}.{PublishedLessons.Fields.edit_data}": {
                "$exists": True
            }
        },
        {
            "$set": {
                f"{PublishedLessons.Fields.parts}.{PublishedLessons.Fields.edit_data}.$[part].{LessonPart.Fields.gcp_path}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.gcp_path}": {"$exists": False}}],
    )

    db.PUBLISHED_LESSONS_COLLECTION.update_many(
        {
            f"{PublishedLessons.Fields.parts}.{PublishedLessons.Fields.edit_data}": {
                "$exists": True
            }
        },
        {
            "$set": {
                f"{PublishedLessons.Fields.parts}.{PublishedLessons.Fields.edit_data}.$[part].{LessonPart.Fields.type_}": LessonPart.Types.NORMAL.value,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.type_}": {"$exists": False}}],
    )

    db.PUBLISHED_LESSONS_COLLECTION.update_many(
        {
            f"{PublishedLessons.Fields.parts}.{PublishedLessons.Fields.edit_data}": {
                "$exists": True
            }
        },
        {
            "$set": {
                f"{PublishedLessons.Fields.parts}.{PublishedLessons.Fields.edit_data}.$[part].{LessonPart.Fields.panoramic_url}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.panoramic_url}": {"$exists": False}}],
    )


def add_lesson_part_type_and_gcp_path_for_archive_lessons():
    db.ARCHIVE_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{ArchiveLessons.Fields.parts}.$[part].{LessonPart.Fields.type_}": LessonPart.Types.NORMAL.value,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.type_}": {"$exists": False}}],
    )

    db.ARCHIVE_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{ArchiveLessons.Fields.parts}.$[part].{LessonPart.Fields.gcp_path}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.gcp_path}": {"$exists": False}}],
    )

    db.ARCHIVE_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{ArchiveLessons.Fields.parts}.$[part].{LessonPart.Fields.panoramic_url}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.panoramic_url}": {"$exists": False}}],
    )

    db.ARCHIVE_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{ArchiveLessons.Fields.parts}.{ArchiveLessons.Fields.edit_data}.$[part].{LessonPart.Fields.gcp_path}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.gcp_path}": {"$exists": False}}],
    )

    db.ARCHIVE_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{ArchiveLessons.Fields.parts}.{ArchiveLessons.Fields.edit_data}.$[part].{LessonPart.Fields.type_}": LessonPart.Types.NORMAL.value,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.type_}": {"$exists": False}}],
    )

    db.ARCHIVE_LESSONS_COLLECTION.update_many(
        {},
        {
            "$set": {
                f"{ArchiveLessons.Fields.parts}.{ArchiveLessons.Fields.edit_data}.$[part].{LessonPart.Fields.panoramic_url}": None,
            }
        },
        array_filters=[{f"part.{LessonPart.Fields.panoramic_url}": {"$exists": False}}],
    )
