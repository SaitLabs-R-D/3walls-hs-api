from enum import Enum
from helpers.fields import ObjectIdField
from pydantic import Field, BaseModel
from .common import DBModel, MongoIndex
from typing import Union

# need to rate all of them
class RatingNames(str, Enum):
    OPERATION = "operation"
    PERTICIPATION = "participation"
    EXPERIENCE = "experience"
    KNOWLEDGE = "knowledge"
    RECOMMENDATION = "recommendation"

    def label(self):
        if self == self.OPERATION:
            return "אופן התפעול – קל עד מסובך"
        elif self == self.PERTICIPATION:
            return "רמת השתתפות התלמידים"
        elif self == self.EXPERIENCE:
            return "רמת החוויה של התלמידים"
        elif self == self.KNOWLEDGE:
            return "רמת הלמידה של התלמידים"
        elif self == self.RECOMMENDATION:
            return "עד כמה הייתם ממליצים"
        else:
            raise ValueError("Invalid enum value")


class Positions(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    OTHER = "other"

    def label(self):
        if self == self.TEACHER:
            return "מורה"
        elif self == self.STUDENT:
            return "תלמיד"
        elif self == self.INSTRUCTOR:
            return "מדריך"
        elif self == self.OTHER:
            return "אחר"
        else:
            raise ValueError("Invalid enum value")


class Ratings(BaseModel):
    name: RatingNames = Field(...)
    label: str = Field(...)
    # between 1 and 5, I am not using pydantic's int validator on purpose
    rating: int = Field(...)

    class Fields(str, Enum):
        name = "name"
        label = "label"
        rating = "rating"


class ReviewrInfo(BaseModel):
    name: str = Field(...)
    institution: str = Field(...)
    position: Positions = Field(...)

    class Fields(str, Enum):
        name = "name"
        institution = "institution"
        position = "position"


class LessonsReviews(DBModel):
    ratings: list[Ratings] = Field(...)
    lesson: Union[ObjectIdField, "PublishedLessons", "ArchiveLessons"] = Field(...)
    user: Union[ObjectIdField, "Users"] = Field(...)
    reviewer: ReviewrInfo = Field(...)
    # review id will be generated for each lesson token, so each
    # lesson view can only contribute one review
    review_id: str = Field(...)
    # free text review
    comments: str = Field(...)

    @classmethod
    def get_indexes(cls) -> list[MongoIndex]:
        unique_review_id = (
            MongoIndex(
                "unique_review_id",
            )
            .add_field(cls.Fields.review_id, 1)
            .set_unique()
        )

        return [unique_review_id]

    class Fields(str, Enum):
        id = "_id"
        ratings = "ratings"
        lesson = "lesson"
        user = "user"
        reviewer = "reviewer"
        review_id = "review_id"
        comments = "comments"


from .lessons import PublishedLessons, ArchiveLessons
from .users import Users


LessonsReviews.update_forward_refs()
