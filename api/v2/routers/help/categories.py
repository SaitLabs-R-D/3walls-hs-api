from fastapi import APIRouter, Depends, Path
from ...middleware import (
    check_user_permission,
    Actions,
    Resources,
    pagintor,
)
from helpers.types import (
    responses,
    RequestWithPagination,
    RequestWithFullUser,
)
from db import queries, inserts, updates, transactions
from helpers import fields
from . import models

router = APIRouter()


@router.get("", dependencies=[Depends(pagintor)])
def get_all_help_categories(
    request: RequestWithPagination,
):

    categoires_res = queries.get_site_help_categories_for_external(request)

    if categoires_res.failure:
        return responses.ApiError(
            code=500, message="something went wrong while getting categories"
        )

    return responses.PaginationResponse(
        data=categoires_res.value[0], count=categoires_res.value[1]
    )


@router.post(
    "",
    dependencies=[
        Depends(
            check_user_permission({Resources.SITE_HELP_CATEGORIES: [Actions.CREATE]})
        )
    ],
)
def create_help_category(
    request: RequestWithFullUser,
    payload: models.NewSiteHelpCategoryPayload,
):
    insert_res = inserts.insert_new_site_help_category(
        name=payload.name,
        description=payload.description,
    )

    if insert_res.failure:
        if insert_res.exists:
            return responses.ApiError(
                409, f"Help category with name {payload.name} already exists"
            )

        return responses.ApiError(500, "Failed to create help category")

    category = insert_res.value

    return responses.ApiSuccess(data=category)


@router.put(
    "/{category_id}",
    dependencies=[
        Depends(
            check_user_permission({Resources.SITE_HELP_CATEGORIES: [Actions.UPDATE]})
        )
    ],
)
def update_help_category(
    request: RequestWithFullUser,
    payload: models.UpdateSiteHelpCategorPayload,
    category_id: fields.ObjectIdField = Path(...),
):

    update_res = updates.update_site_help_category_by_id(
        category_id,
        name=payload.name,
        description=payload.description,
    )

    if update_res.failure:
        if update_res.exists:
            return responses.ApiError(
                code=409, message="category with this name already exists"
            )
        return responses.ApiError(
            code=500, message="something went wrong while updating category"
        )

    return responses.ApiSuccess(code=200, message="category updated successfully")


@router.delete(
    "/{category_id}",
    dependencies=[
        Depends(
            check_user_permission({Resources.SITE_HELP_CATEGORIES: [Actions.DELETE]})
        )
    ],
)
def delete_help_category(
    request: RequestWithFullUser, category_id: fields.ObjectIdField = Path(...)
):

    tran_res = transactions.delete_site_help_category(category_id)

    if not tran_res.success:
        return responses.ApiError(
            code=500, message="something went wrong while deleting category"
        )

    return responses.ApiSuccess(code=200, message="successfully deleted category")
