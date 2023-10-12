from helpers.types import RequestWithFullUser
from db.models import SiteHelp, SiteHelpCategories
from db import updates
from db.inserts.site_help import _insert_new_site_help
from typing import Union, Optional
from bson import ObjectId
from services.gcp import GCP_MANAGER
from .common import Transaction, TransactionResult, ClientSession
import io, db
from helpers.files import get_file_extension_from_mime_type
from .. import updates


def add_new_site_help(
    background_image: tuple[io.BytesIO, str],
    title: str,
    pdf: Optional[tuple[io.BytesIO, str]],
    youtube_link: Optional[str],
    category: Union[str, ObjectId, SiteHelpCategories],
    description: str,
    request: RequestWithFullUser,
) -> Optional[TransactionResult[SiteHelp]]:
    def the_tran(
        session: ClientSession,
        background_image: tuple[io.BytesIO, str],
        title: str,
        pdf: Optional[tuple[io.BytesIO, str]],
        youtube_link: Optional[str],
        category: Union[str, ObjectId, SiteHelpCategories],
        description: str,
        request: RequestWithFullUser,
    ):
        if isinstance(category, SiteHelpCategories):
            category = category.id

        try:
            order = db.SITE_HELP_COLLECTION.count_documents({})
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to get site help count",
            )
        site_help = SiteHelp(
            title=title,
            youtube_link=youtube_link,
            category=ObjectId(category),
            description=description,
            creator=request.state.user.id,
            order=order,
        )

        insert_res = _insert_new_site_help(site_help, session=session)

        if insert_res.failure:
            return TransactionResult(
                success=False,
                message="Failed to insert new site help",
            )

        site_help = insert_res.value

        background_image_link = None

        try:
            file_type = get_file_extension_from_mime_type(background_image[1])

            background_image_link = GCP_MANAGER.upload_site_help_background_image(
                background_image[0], str(site_help.id), file_type, background_image[1]
            )
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to upload background image",
            )

        pdf_link = None

        if pdf:
            try:
                file_type = get_file_extension_from_mime_type(pdf[1])

                pdf_link = GCP_MANAGER.upload_site_help_pdf(
                    pdf[0],
                    str(site_help.id),
                )
            except Exception as e:
                print(e)
                return TransactionResult(
                    success=False,
                    message="Failed to upload pdf",
                )

        update_res = updates.update_site_help_by_id(
            site_help,
            pdf=pdf_link,
            background_image=background_image_link,
            session=session,
            return_document=True,
        )

        if update_res.failure:
            return TransactionResult(
                success=False,
                message="Failed to update site help",
            )

        site_help = update_res.value

        return TransactionResult(success=True, value=site_help)

    transaction = Transaction(
        func=the_tran,
        args=[
            background_image,
            title,
            pdf,
            youtube_link,
            category,
            description,
            request,
        ],
        kwargs={},
    )

    transaction.start()

    return transaction.result


def delete_site_help_pdf_file(
    site_help_id: Union[str, ObjectId],
) -> Optional[TransactionResult[SiteHelp]]:
    def the_tran(
        session: ClientSession,
        site_help_id: SiteHelp,
    ):
        try:
            site_help = db.SITE_HELP_COLLECTION.find_one_and_update(
                {
                    SiteHelp.Fields.id: ObjectId(site_help_id),
                    SiteHelp.Fields.pdf: {"$type": "string"},
                },
                {
                    "$set": {
                        SiteHelp.Fields.pdf: None,
                    }
                },
                session=session,
            )
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to get site help",
            )

        if not site_help:
            return TransactionResult(
                success=False,
                message="Site help not found",
            )

        site_help = SiteHelp(**site_help)

        try:
            GCP_MANAGER.delete_site_help_pdf(site_help.id)
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to delete pdf",
            )
        site_help.pdf = None
        return TransactionResult(success=True, value=site_help)

    transaction = Transaction(
        func=the_tran,
        args=[
            site_help_id,
        ],
        kwargs={},
    )

    transaction.start()

    return transaction.result


def delete_site_help(
    site_help_id: Union[str, ObjectId],
) -> Optional[TransactionResult[SiteHelp]]:
    def the_tran(
        session: ClientSession,
        site_help_id: Union[str, ObjectId],
    ):

        try:
            site_help = db.SITE_HELP_COLLECTION.find_one_and_delete(
                {
                    SiteHelp.Fields.id: ObjectId(site_help_id),
                },
                session=session,
            )
        except Exception as e:
            return TransactionResult(
                success=False,
                message="Failed to get site help",
            )

        if not site_help:
            return TransactionResult(
                success=False,
                message="Site help not found",
            )

        site_help = SiteHelp(**site_help)

        # update order
        try:
            db.SITE_HELP_COLLECTION.update_many(
                {
                    SiteHelp.Fields.order: {"$gt": site_help.order},
                },
                {
                    "$inc": {
                        SiteHelp.Fields.order: -1,
                    }
                },
                session=session,
            )
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to update site help order",
            )

        try:
            GCP_MANAGER.delete_site_help_folder(site_help_id)
        # There cant be not found error because the background image is required
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to delete site help folder",
            )

        return TransactionResult(success=True, value=site_help)

    transaction = Transaction(
        func=the_tran,
        args=[
            site_help_id,
        ],
        kwargs={},
    )

    transaction.start()

    return transaction.result


def delete_site_help_category(
    category_id: Union[str, ObjectId],
):
    def the_tran(
        session: ClientSession,
        category_id: Union[str, ObjectId],
    ):

        try:
            site_help_category = db.SITE_HELP_CATEGORIES_COLLECTION.find_one_and_delete(
                {
                    SiteHelpCategories.Fields.id: ObjectId(category_id),
                },
                session=session,
            )
        except Exception as e:
            return TransactionResult(
                success=False,
                message="Failed to get site help category",
            )

        if not site_help_category:
            return TransactionResult(
                success=False,
                message="Site help category not found",
            )
        try:
            res = db.SITE_HELP_COLLECTION.update_many(
                {
                    SiteHelp.Fields.category: ObjectId(category_id),
                },
                {
                    "$set": {
                        SiteHelp.Fields.category: None,
                    }
                },
            )
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to update site help category",
            )

        return TransactionResult(success=True, value=site_help_category)

    transaction = Transaction(
        func=the_tran,
        args=[
            category_id,
        ],
        kwargs={},
    )

    transaction.start()

    return transaction.result


def reorder_site_help(
    help_id: Union[str, ObjectId],
    new_order: int,
):
    def the_tran(
        session: ClientSession,
        help_id: Union[str, ObjectId],
        new_order: int,
    ):
        if new_order < 0:
            return TransactionResult(
                success=False,
                message="New order must be greater than 0",
            )
        # will return the site help before the update
        site_help = updates.update_site_help_by_id(
            help_id, order=new_order, session=session
        )

        if site_help.failure:
            return TransactionResult(
                success=False,
                message="Failed to get site help",
            )

        site_help = site_help.value

        if site_help.order == new_order:
            return TransactionResult(
                success=True,
                value=site_help,
            )

        query = {}
        update = {}
        # if its smaller than the new order then we need to increment all the ones in between
        if site_help.order < new_order:
            query = {
                SiteHelp.Fields.order: {
                    "$gt": site_help.order,
                    "$lte": new_order,
                }
            }

            update = {
                "$inc": {
                    SiteHelp.Fields.order: -1,
                }
            }

        else:
            query = {
                SiteHelp.Fields.order: {
                    "$gte": new_order,
                    "$lt": site_help.order,
                }
            }

            update = {
                "$inc": {
                    SiteHelp.Fields.order: 1,
                }
            }

        # To not update the current site help
        query.update(
            {
                SiteHelp.Fields.id: {
                    "$ne": site_help.id,
                }
            }
        )

        try:
            db.SITE_HELP_COLLECTION.update_many(
                query,
                update,
                session=session,
            )
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to update site help",
            )

        return TransactionResult(success=True, value=site_help)

    transaction = Transaction(
        func=the_tran,
        args=[help_id, new_order],
        kwargs={},
    )

    transaction.start()

    return transaction.result
