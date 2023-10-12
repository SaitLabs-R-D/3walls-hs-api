from fastapi import APIRouter, Depends, Path, BackgroundTasks
from ...middleware import (
    login_required,
    check_user_permission,
    Actions,
    Resources,
    pagintor,
)
from helpers.types import (
    responses,
    RequestWithFullUser,
    RequestWithPagination,
)
from db import queries, transactions, queries, updates
from helpers import fields
from . import categories, models
from services.gcp import GCP_MANAGER
from helpers.files import get_file_extension_from_mime_type

router = APIRouter(
    dependencies=[
        Depends(login_required),
    ]
)

router.include_router(categories.router, prefix="/categories")


@router.get(
    "",
    dependencies=[
        Depends(pagintor),
    ],
)
def get_all_site_help(
    request: RequestWithPagination,
    query: models.GetSiteHelpQueryParams = Depends(),
):

    site_help_res = queries.get_site_helps_for_external(
        category_id=query.category,
        list_view=query.list_view,
        request=request,
    )

    if site_help_res.failure:
        return responses.ApiError(
            code=500, message="something went wrong while getting site helps"
        )

    return responses.PaginationResponse(
        data=site_help_res.value[0],
        count=site_help_res.value[1],
    )


@router.post(
    "",
    dependencies=[
        Depends(check_user_permission({Resources.SITE_HELP: [Actions.CREATE]}))
    ],
)
def create_site_help(
    request: RequestWithFullUser,
    payload: models.NewSiteHelpPayload,
):

    category = queries.get_site_help_category_by_id(payload.category)

    if category.failure:
        if category.not_found:
            return responses.ApiError(
                code=404, message="category with this id does not exist"
            )
        return responses.ApiError(
            code=500, message="failed to get category with this id"
        )

    add_res = transactions.add_new_site_help(
        background_image=payload.background_image,
        title=payload.title,
        pdf=payload.pdf,
        youtube_link=payload.youtube_link,
        category=payload.category,
        description=payload.description,
        request=request,
    )

    if not add_res or not add_res.success:
        return responses.ApiError(
            code=500, message="something went wrong while creating site help"
        )

    return responses.ApiSuccess(data=add_res.value)


@router.put(
    "/reorder",
    dependencies=[
        Depends(check_user_permission({Resources.SITE_HELP: [Actions.UPDATE]}))
    ],
)
def reorder_site_help(
    request: RequestWithFullUser, payload: models.ReorderSiteHelpPayload
):

    res = transactions.reorder_site_help(
        help_id=payload.site_help_id,
        new_order=payload.new_order,
    )

    if not res or not res.success:
        return responses.ApiError(
            code=500, message="something went wrong while deleting site help pdf file"
        )

    return responses.ApiSuccess(data=res.value)


@router.get("/{site_help_id}")
def get_site_help(
    site_help_id: fields.ObjectIdField = Path(...),
):

    site_help_res = queries.get_site_help_by_id(site_help_id)

    if site_help_res.failure:
        if site_help_res.not_found:
            return responses.ApiError(
                code=404, message="site help with this id does not exist"
            )
        return responses.ApiError(
            code=500, message="something went wrong while getting site help"
        )

    site_help = site_help_res.value

    if site_help.pdf:
        site_help.pdf = GCP_MANAGER.bucket_manager.generate_file_download_url(
            site_help.pdf
        )

    return responses.ApiSuccess(data=site_help)


@router.put(
    "/{site_help_id}",
    dependencies=[
        Depends(check_user_permission({Resources.SITE_HELP: [Actions.UPDATE]}))
    ],
)
def edit_site_help(
    request: RequestWithFullUser,
    payload: models.EditSiteHelpPayload,
    site_help_id: fields.ObjectIdField = Path(...),
):

    if payload.category:
        res = queries.get_site_help_category_by_id(payload.category)

        if res.failure:
            if res.not_found:
                return responses.ApiError(
                    code=404, message="category with this id does not exist"
                )
            return responses.ApiError(
                code=500,
                message="something went wrong while getting category with this id",
            )

    site_help = queries.get_site_help_by_id(site_help_id)

    if site_help.failure:
        if site_help.not_found:
            return responses.ApiError(
                code=404, message="site help with this id does not exist"
            )
        return responses.ApiError(
            code=500, message="something went wrong while getting site help"
        )

    if payload.pdf:
        GCP_MANAGER.upload_site_help_pdf(
            payload.pdf[0],
            site_help_id,
        )

    if payload.background_image:
        payload.background_image = GCP_MANAGER.upload_site_help_background_image(
            payload.background_image[0],
            site_help_id,
            get_file_extension_from_mime_type(payload.background_image[1]),
            payload.background_image[1],
        )

    update_res = updates.update_site_help_by_id(
        id=site_help_id,
        title=payload.title,
        description=payload.description,
        youtube_link=payload.youtube_link,
        category=payload.category,
        background_image=payload.background_image,
        return_document=True,
    )

    if update_res.failure:
        return responses.ApiError(
            code=500, message="something went wrong while updating site help"
        )

    return responses.ApiSuccess(data=update_res.value)


@router.delete(
    "/{site_help_id}",
    dependencies=[
        Depends(check_user_permission({Resources.SITE_HELP: [Actions.DELETE]}))
    ],
)
def delete_site_help(
    request: RequestWithFullUser,
    site_help_id: fields.ObjectIdField = Path(...),
):

    tran_res = transactions.delete_site_help(
        site_help_id=site_help_id,
    )

    if not tran_res.success:
        return responses.ApiError(
            code=500, message="something went wrong while deleting site help"
        )

    return responses.ApiSuccess(data=tran_res.value)


@router.delete(
    "/{site_help_id}/pdf",
    dependencies=[
        Depends(check_user_permission({Resources.SITE_HELP: [Actions.DELETE]}))
    ],
)
def delete_site_help_pdf_file(
    request: RequestWithFullUser,
    site_help_id: fields.ObjectIdField = Path(...),
):

    res = transactions.delete_site_help_pdf_file(
        site_help_id=site_help_id,
    )

    if not res.success:
        return responses.ApiError(
            code=500, message="something went wrong while deleting site help pdf file"
        )

    return responses.ApiSuccess(data=res.value)
