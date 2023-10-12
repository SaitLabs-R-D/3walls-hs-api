from pydantic import BaseModel, Field
from db.models import LessonsReviews, RatingNames, ReviewrInfo, Ratings, Positions


class CreateReviewPayload(BaseModel):
    class ReviewrInfo_(BaseModel):
        name: str
        institution: str
        position: Positions

    class Ratings_(BaseModel):
        key: RatingNames
        value: int = Field(..., gt=0, lt=6)

    token: str
    comment: str
    ratings: list[Ratings_] = Field(
        ..., min_items=len(RatingNames), max_items=len(RatingNames)
    )
    reviewer_info: ReviewrInfo_
