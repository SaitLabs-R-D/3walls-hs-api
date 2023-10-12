from fastapi import APIRouter, Depends, Path, BackgroundTasks, Query
from db import queries, updates, inserts, transactions
from ...middleware import (
    login_required,
    check_user_permission,
    Actions,
    Resources,
    pagintor,
)
from helpers.files import get_file_extension_from_mime_type
from services.gcp import GCP_MANAGER
from services.sendgrid import EMAIL_SERVICE
from . import models
from helpers.types import (
    responses,
    RequestWithPaginationAndFullUser,
    RequestWithFullUser,
)
from helpers.secuirty import passwords, tokens
from helpers import fields
from typing import Optional

router = APIRouter(dependencies=[Depends(login_required)])


@router.post(
    "",
    dependencies=[
        Depends(
            check_user_permission(
                {
                    Resources.ACCOUNTS: [Actions.CREATE],
                    Resources.USERS: [Actions.CREATE],
                    Resources.PUBLISHED_LESSONS: [Actions.READ],
                    Resources.CATEGORIES: [Actions.READ],
                }
            )
        )
    ],
)
def create_new_account(
    request: RequestWithFullUser,
    payload: models.CreateAccountPayload,
    background_tasks: BackgroundTasks,
):

    content_type = None
    file_type = None
    logo_file = None

    if payload.logo is not None:

        logo_file, content_type = payload.logo

        file_type = get_file_extension_from_mime_type(content_type)

        if not file_type:
            return responses.ApiError(code=400, message="invalid image file")

    # To make sure that even if the query fails, we don't create the account
    # we proceed only if the query return user not found
    if not queries.get_user_by_email(payload.email).not_found:
        return responses.ApiError(code=409, message="email already in use")

    if payload.lessons:
        check_lessons_result = queries.validate_published_lessons_exists(
            payload.lessons
        )
        if check_lessons_result.failure:
            if check_lessons_result.not_found:
                return responses.ApiError(code=404, message="lessons not found")
            return responses.ApiError(code=500, message="error while checking lessons")

    if payload.categories:
        check_categories_result = queries.validate_categories_exists(payload.categories)
        if check_categories_result.failure:
            if check_categories_result.not_found:
                return responses.ApiError(code=404, message="categories not found")
            return responses.ApiError(
                code=500, message="error while checking categories"
            )

    # create the new account
    new_account = inserts.insert_new_account(
        institution_name=payload.institution_name,
        city=payload.city,
        contact_man_name=f"{payload.contact_man_first_name} {payload.contact_man_last_name}",
        email=payload.email,
        phone=payload.phone,
        allowed_users=payload.allowed_users,
        allowed_lessons=payload.lessons,
        allowed_categories=payload.categories,
    )

    if not new_account.success:
        if new_account.exists:
            return responses.ApiError(code=409, message="account already exists")

        return responses.ApiError(code=400, message="error while creating account")

    new_account = new_account.value

    if file_type and logo_file and content_type:
        logo_url = GCP_MANAGER.upload_account_logo(
            logo_file, str(new_account.id), file_type, content_type
        )

        updates.update_account_by_id(new_account.id, logo=logo_url)

    def create_new_account_manager(
        data: models.CreateAccountPayload,
        new_account,
    ):

        account_manager_role = queries.get_account_manager_role()

        if not account_manager_role.success:
            # TODO log error
            return

        # create the new user
        new_user = inserts.insert_new_account_manager_user(
            account_manager_role.value,
            new_account.id,
            email=data.email,
            password=passwords.hash_password(passwords.generate_password()),
            first_name=data.contact_man_first_name,
            last_name=data.contact_man_last_name,
            phone_number=data.phone,
        )

        if not new_user.success:
            # TODO log error
            return

        new_user = new_user.value

        if updates.update_account_current_users_count(new_user.account, 1).failure:
            # TODO log error
            pass

        token = tokens.generate_first_login_token(str(new_user.id))

        EMAIL_SERVICE.send_regstration_email(
            new_user.email, new_user.email, new_user.full_name, token
        )

        updates.set_user_registration_token(new_user.id, token)

    background_tasks.add_task(create_new_account_manager, payload, new_account)

    return responses.ApiSuccess(
        message="account created successfully", data=new_account
    )


@router.get(
    "",
    dependencies=[
        Depends(pagintor),
        Depends(
            check_user_permission(
                {
                    Resources.ACCOUNTS: [Actions.READ_MANY],
                }
            )
        ),
    ],
)
def get_all_accounts(request: RequestWithPaginationAndFullUser):

    accounts_res = queries.get_accounts_for_external(
        request,
    )

    if accounts_res.failure:
        return responses.ApiError(code=500, message="error while fetching accounts")

    data, count = accounts_res.value

    return responses.PaginationResponse(
        data=data,
        count=count,
    )


@router.get(
    "/by-id",
    dependencies=[
        Depends(
            check_user_permission(
                {
                    Resources.ACCOUNTS: [Actions.READ],
                }
            )
        ),
    ],
)
def get_account_by_id(
    request: RequestWithFullUser,
    # we use query param beacuse we want to allow to get their own account
    # without knowing the account id
    account_id: Optional[fields.ObjectIdField] = Query(None),
):

    account_id = account_id or request.state.user.account

    if not account_id:
        return responses.ApiError(code=400, message="account id is required")

    account_res = queries.get_account_by_id_for_external(request, account_id)

    if account_res.failure:
        if account_res.not_found:
            return responses.ApiError(code=404, message="account not found")
        return responses.ApiError(code=500, message="error while fetching accounts")

    return responses.ApiSuccess(data=account_res.value)


@router.put(
    "",
    dependencies=[
        Depends(
            check_user_permission(
                {
                    Resources.ACCOUNTS: [Actions.UPDATE],
                    Resources.PUBLISHED_LESSONS: [Actions.READ],
                    Resources.CATEGORIES: [Actions.READ],
                }
            )
        ),
    ],
)
def update_account_by_id(
    request: RequestWithFullUser,
    payload: models.UpdateAccountPayload,
    background_tasks: BackgroundTasks,
    # we use query param beacuse we want to allow to update their own account
    # without knowing the account id
    account_id: Optional[fields.ObjectIdField] = Query(None),
):

    account_id = account_id or request.state.user.account

    if not account_id:
        return responses.ApiError(code=400, message="account id is required")

    content_type = None
    file_type = None
    logo_file = None

    if payload.logo is not None:

        logo_file, content_type = payload.logo

        file_type = get_file_extension_from_mime_type(content_type)

        if not file_type:
            return responses.ApiError(code=400, message="invalid image file")

    if payload.lessons:
        check_lessons_result = queries.validate_published_lessons_exists(
            payload.lessons
        )
        if check_lessons_result.failure:
            if check_lessons_result.not_found:
                return responses.ApiError(code=404, message="lessons not found")
            return responses.ApiError(code=500, message="error while checking lessons")

    if payload.categories:
        check_categories_result = queries.validate_categories_exists(payload.categories)
        if check_categories_result.failure:
            if check_categories_result.not_found:
                return responses.ApiError(code=404, message="categories not found")
            return responses.ApiError(
                code=500, message="error while checking categories"
            )

    updates_res = updates.update_account_by_id(
        account_id,
        request=request,
        allowed_categories=payload.categories,
        allowed_lessons=payload.lessons,
        email=payload.email,
        phone=payload.phone,
        allowed_users=payload.allowed_users,
        city=payload.city,
        institution_name=payload.institution_name,
        contact_man_name=payload.contact_man_name,
    )

    if updates_res.failure:
        if updates_res.not_found:
            return responses.ApiError(code=404, message="account not found")
        if updates_res.not_valid:
            return responses.ApiError(code=400, message="invalid data")
        if updates_res.exists:
            return responses.ApiError(code=409, message="duplicate data")
        return responses.ApiError(code=500, message="error while updating account")

    # If in the future some users cant update the logo
    # we need to remove this from background tasks and add it to the update_account_by_id
    def update_the_logo(
        account_id: str,
        logo_file: bytes,
        file_type: str,
        content_type: str,
    ):
        logo_url = GCP_MANAGER.upload_account_logo(
            logo_file, account_id, file_type, content_type
        )
        # If the update was successful, there is no need to pass the request
        # because the update was alredy validated
        updates.update_account_by_id(account_id, logo=logo_url)

    if file_type and logo_file and content_type:
        background_tasks.add_task(
            update_the_logo, str(account_id), logo_file, file_type, content_type
        )

    return responses.ApiSuccess(message="account updated successfully")


@router.delete(
    "/{account_id}",
    dependencies=[
        Depends(
            check_user_permission(
                {
                    Resources.ACCOUNTS: [Actions.DELETE],
                }
            )
        ),
    ],
)
def delete_account_by_id(
    request: RequestWithFullUser,
    background_tasks: BackgroundTasks,
    account_id: fields.ObjectIdField = Path(...),
):

    if request.state.user.account:
        if request.state.user.account.id == account_id:
            return responses.ApiError(
                code=403, message="you can't delete your own account"
            )

    account_res = queries.get_account_by_id(
        account_id,
        request=request,
    )

    if account_res.failure:
        if account_res.not_found:
            return responses.ApiError(code=404, message="account not found")
        return responses.ApiError(code=500, message="error while getting account")

    background_tasks.add_task(transactions.fully_delete_account, account_id, request)

    return responses.ApiSuccess(message="account deleted successfully")
