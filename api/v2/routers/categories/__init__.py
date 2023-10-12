from fastapi import APIRouter, Depends, Path, BackgroundTasks
from ...middleware import (
    check_user_permission,
    login_required,
    pagintor,
    Actions,
    Resources,
)
from . import models
from db.models import RolesInternalNames
from helpers.types import (
    RequestWithPaginationAndFullUser,
    RequestWithFullUser,
    responses,
)
from helpers import fields
from db import queries, inserts, transactions, updates

router = APIRouter(dependencies=[Depends(login_required)])


@router.get(
    "",
    dependencies=[
        Depends(pagintor),
        Depends(check_user_permission({Resources.CATEGORIES: [Actions.READ_MANY]})),
    ],
)
def get_all_categories(
    request: RequestWithPaginationAndFullUser,
    query: models.GetCategoriesQueryParams = Depends(),
):

    if request.state.user.role.internal_name in [
        RolesInternalNames.GUEST,
        RolesInternalNames.VIEWER,
    ]:
        categoires_res = queries.get_categories_associated_with_user(
            query.free_text, request
        )
    else:
        categoires_res = queries.get_categories_for_external(query.free_text, request)

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
        Depends(check_user_permission({Resources.CATEGORIES: [Actions.CREATE]}))
    ],
)
def create_new_category(
    request: RequestWithFullUser, payload: models.CreateCategoryPayload
):

    create_res = inserts.insert_new_category(
        name=payload.name,
        description=payload.description,
    )

    if create_res.failure:
        if create_res.exists:
            return responses.ApiError(
                code=400, message="category with this name already exists"
            )
        return responses.ApiError(
            code=500, message="something went wrong while creating category"
        )

    return responses.ApiSuccess(code=201, message="category created successfully")


@router.delete(
    "/{category_id}",
    dependencies=[
        Depends(check_user_permission({Resources.CATEGORIES: [Actions.DELETE]}))
    ],
)
def delete_category(
    request: RequestWithFullUser,
    background_tasks: BackgroundTasks,
    category_id: fields.ObjectIdField = Path(...),
):

    background_tasks.add_task(transactions.fully_delete_category, category_id, request)

    return responses.ApiSuccess(code=200, message="category deleted successfully")


@router.put(
    "/{category_id}",
    dependencies=[
        Depends(check_user_permission({Resources.CATEGORIES: [Actions.UPDATE]}))
    ],
)
def update_category(
    request: RequestWithFullUser,
    payload: models.UpdateCategoryPayload,
    category_id: fields.ObjectIdField = Path(...),
):

    update_res = updates.update_category_by_id(
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
