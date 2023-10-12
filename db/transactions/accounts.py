from helpers.types import RequestWithFullUser
from db import updates, queries
from typing import Union
from bson import ObjectId
from services.gcp import GCP_MANAGER
from .common import Transaction, TransactionResult, ClientSession


def fully_delete_account(
    account_id: Union[str, ObjectId], request: RequestWithFullUser
):
    def the_tran(
        session: ClientSession,
        account_id: Union[str, ObjectId],
        request: RequestWithFullUser,
    ):

        draft_ids = []

        # deleting account
        delete_account_res = updates.delete_account_by_id(
            account_id, request, session=session
        )

        if delete_account_res.failure:
            return TransactionResult(
                success=False,
                message="Failed to delete account",
            )

        users_ids_res = queries.get_users_ids_by_account_id(account_id, session=session)

        if users_ids_res.failure:
            print("Failed to get users ids")
            return TransactionResult(
                success=False,
                message="Failed to get users ids",
            )

        users_ids = users_ids_res.value

        if len(users_ids):
            delete_users_res = updates.delete_many_users_by_ids(
                users_ids, request, session=session
            )

            if delete_users_res.failure:
                print("Failed to delete users")
                return TransactionResult(
                    success=False,
                    message="Failed to delete users",
                )

            if not len(users_ids) == delete_users_res.value:
                print("Failed to delete all users")
                return TransactionResult(
                    success=False,
                    message="Failed to delete all users",
                )

            admin_user_res = queries.get_system_admin_user(session=session)

            # If there is no admin user, then we can't delete the account
            # because there will be no one to pass the lessons to
            if admin_user_res.failure:
                print("Failed to get admin user")
                return TransactionResult(
                    success=False,
                    message="Failed to get admin user",
                )

            admin_user = admin_user_res.value

            draft_lessons_res = queries.get_draft_lessons_ids_by_creators(
                users_ids, session=session
            )

            if draft_lessons_res.failure:
                print("Failed to get draft lessons ids")
                return TransactionResult(
                    success=False,
                    message="Failed to get draft lessons ids",
                )

            draft_ids = draft_lessons_res.value

            if len(draft_ids):
                # deleting draft lessons
                if updates.delete_many_draft_lessons_by_creatores_ids(
                    users_ids, session=session
                ).failure:
                    print("Failed to delete draft lessons")
                    return TransactionResult(
                        success=False,
                        message="Failed to delete draft lessons",
                    )
                # changing the creator of the users published and archived lessons to the admin user
                if updates.change_many_published_lessons_creator(
                    users_ids, admin_user.id, session=session
                ).failure:
                    return TransactionResult(
                        success=False,
                        message="Failed to change published lessons creator",
                    )

                if updates.change_many_archived_lessons_creator(
                    users_ids, admin_user.id, session=session
                ).failure:

                    return TransactionResult(
                        success=False,
                        message="Failed to change archived lessons creator",
                    )

                if (
                    updates.change_many_editors_of_published_lessons(
                        users_ids, admin_user.id, session=session
                    )
                ).failure:
                    return TransactionResult(
                        success=False,
                        message="Failed to change editors of published lessons",
                    )

                if (
                    updates.change_many_editors_of_archived_lessons(
                        users_ids, admin_user.id, session=session
                    )
                ).failure:
                    return TransactionResult(
                        success=False,
                        message="Failed to change editors of archived lessons",
                    )

                if updates.change_many_archived_by_of_archived_lessons(
                    users_ids, admin_user.id, session=session
                ).failure:
                    return TransactionResult(
                        success=False,
                        message="Failed to change archived by of archived lessons",
                    )

        try:
            GCP_MANAGER.delete_account_folder(str(account_id))
        except Exception as e:
            print(e)
            return TransactionResult(
                success=False,
                message="Failed to delete account storage folder",
            )

        for draft in draft_ids:
            try:
                GCP_MANAGER.delete_lesson(str(draft))
            except:
                # TODO log error with the draft id, to delete it later
                pass

        return TransactionResult(success=True)

    transaction = Transaction(func=the_tran, args=[account_id, request], kwargs={})

    transaction.start()
