from fastapi import APIRouter, Depends, Path, Request
from db.models import RatingNames, Ratings, Positions
from ...middleware import login_required, check_user_permission, Resources, Actions
from helpers.types import responses, RequestWithFullUser
from helpers import fields
from helpers.secuirty import tokens
from . import models
from db import inserts, queries, updates

router = APIRouter()


@router.get("/metadata")
def reviews_meta_data(_: Request):

    ratings_fields = []

    for rating in RatingNames:
        ratings_fields.append({"key": rating.value, "label": rating.label()})

    positions_fields = []

    for position in Positions:
        positions_fields.append({"key": position.value, "label": position.label()})

    return responses.ApiSuccess(
        data={"ratings": ratings_fields, "positions": positions_fields}
    )


@router.post("")
def create_review(_: Request, payload: models.CreateReviewPayload):

    token_res = tokens.decode_watch_token(payload.token)

    if token_res.failure:
        return responses.ApiError(code=403, message="Invalid token")

    token_data = token_res.value

    if not token_data.lesson_type == "published":
        return responses.ApiError(code=403, message="Invalid token")

    ratings = []

    for rating in payload.ratings:
        ratings.append(
            Ratings(
                name=rating.key.value, label=rating.key.label(), rating=rating.value
            )
        )

    review_res = inserts.insert_new_lesson_review(
        ratings=ratings,
        lesson=token_data.lesson_id,
        user=token_data.issuer,
        reviewer_name=payload.reviewer_info.name,
        reviewer_institution=payload.reviewer_info.institution,
        reviewer_position=payload.reviewer_info.position,
        review_id=token_data.id,
        comments=payload.comment,
    )

    if review_res.failure:
        if review_res.exists:
            return responses.ApiError(
                code=409, message="You already reviewed this lesson"
            )
        return responses.ApiError(code=500, message="Failed to create review")

    return responses.ApiSuccess(data={"_id": review_res.value.id})


@router.get(
    "/{lesson_id}",
    dependencies=[
        Depends(login_required),
        Depends(check_user_permission({Resources.REVIEWS: [Actions.READ_MANY]})),
    ],
)
def get_all_reviews(
    request: RequestWithFullUser,
    lesson_id: fields.ObjectIdField = Path(...),
):
    # user can get reviews only for published lessons that he can read
    lesson_res = queries.get_published_lesson_by_id(lesson_id, request)

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(code=404, message="Lesson not found")
        return responses.ApiError(code=500, message="Failed to get lesson")

    reviews_res = queries.get_lessons_review_for_external(lesson_id)

    if reviews_res.failure:
        return responses.ApiError(code=500, message="Failed to get reviews")

    return responses.ApiSuccess(data=reviews_res.value)


@router.delete(
    "/{review_id}",
    dependencies=[
        Depends(login_required),
        Depends(check_user_permission({Resources.REVIEWS: [Actions.DELETE]})),
    ],
)
def delete_review(
    _: RequestWithFullUser,
    review_id: fields.ObjectIdField = Path(...),
):

    delete_res = updates.delete_review_by_id(review_id)

    if delete_res.failure:
        if delete_res.not_found:
            return responses.ApiError(code=404, message="Review not found")
        return responses.ApiError(code=500, message="Failed to delete review")

    return responses.ApiSuccess(data={"_id": review_id})
