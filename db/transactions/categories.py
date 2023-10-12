from helpers.types import RequestWithFullUser
from db import updates, queries
from typing import Union
from bson import ObjectId
from services.gcp import GCP_MANAGER
from .common import Transaction, TransactionResult, ClientSession
from db.models import (
    Categories,
    PublishedLessons,
    DraftLessons,
    ArchiveLessons,
)
import db


def fully_delete_category(
    category_id: Union[str, ObjectId], request: RequestWithFullUser
):
    def the_tran(
        session: ClientSession,
        category_id: Union[str, ObjectId],
        request: RequestWithFullUser,
    ):

        try:
            res = db.CATEGORIES_COLLECTION.delete_one(
                {Categories.Fields.id: ObjectId(category_id)}, session=session
            )
        except:
            return TransactionResult(success=False, message="Failed to delete category")

        if not res.deleted_count == 1:
            return TransactionResult(success=False, message="lesson not found")

        category_id = ObjectId(category_id)

        try:
            res = db.PUBLISHED_LESSONS_COLLECTION.update_many(
                {PublishedLessons.Fields.categories: {"$in": [category_id]}},
                {"$pull": {PublishedLessons.Fields.categories: category_id}},
            )
        except:
            return TransactionResult(
                success=False, message="Failed to update published lessons"
            )

        try:
            res = db.DRAFT_LESSONS_COLLECTION.update_many(
                {DraftLessons.Fields.categories: {"$in": [category_id]}},
                {"$pull": {DraftLessons.Fields.categories: category_id}},
            )
        except:
            return TransactionResult(
                success=False, message="Failed to update draft lessons"
            )

        try:
            res = db.ARCHIVE_LESSONS_COLLECTION.update_many(
                {ArchiveLessons.Fields.categories: {"$in": [category_id]}},
                {"$pull": {ArchiveLessons.Fields.categories: category_id}},
            )
        except:
            return TransactionResult(
                success=False, message="Failed to update archive lessons"
            )

        return TransactionResult(success=True)

    transaction = Transaction(func=the_tran, args=[category_id, request], kwargs={})

    transaction.start()
