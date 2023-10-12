from typing import TypeVar, Generic, Type, Union
from helpers.types import responses, errors
from pydantic import BaseModel, Field, root_validator
from db import aggregations
from db.models.lessons.common import BaseLessonFields

T = TypeVar("T")


class QueryResults(Generic[T]):
    def __init__(
        self,
        success: bool = False,
        failure: bool = False,
        not_found: bool = False,
        value: T = None,
    ):
        self.value = value
        self.success = success
        self.failure = failure or not_found
        self.not_found = not_found

    def into_response(
        self,
        message: str = "",
        error_code: errors.ErrorType = errors.ErrorType.FAILD_QUERY,
    ) -> Type[responses._Response]:
        if self.failure:
            return responses.ApiError(message=message, error_code=error_code)
        if self.not_found:
            return responses.ApiError(message=message, error_code=error_code)


class InsertResults(Generic[T]):
    def __init__(
        self,
        success: bool = False,
        failure: bool = False,
        exists: bool = False,
        not_valid: bool = False,
        value: T = None,
    ):
        self.value = value
        self.success = success
        self.failure = failure or exists or not_valid
        self.exists = exists
        self.not_valid = not_valid

    def into_response(
        self,
        message: str = "",
        error_code: errors.ErrorType = errors.ErrorType.FAILD_QUERY,
    ) -> Type[responses._Response]:
        if self.failure:
            return responses.ApiError(message=message, error_code=error_code)
        if self.exists:
            return responses.ApiError(message=message, error_code=error_code, code=409)


class UpdateResults(Generic[T]):
    def __init__(
        self,
        success: bool = False,
        failure: bool = False,
        not_found: bool = False,
        not_valid: bool = False,
        exists: bool = False,
        value: T = None,
    ):
        self.value = value
        self.success = success
        self.failure = failure or not_found or not_valid or exists
        self.not_found = not_found
        self.not_valid = not_valid
        self.exists = exists

    def into_response(
        self,
        message: str = "",
        error_code: errors.ErrorType = errors.ErrorType.FAILD_QUERY,
    ) -> Type[responses._Response]:
        if self.failure:
            return responses.ApiError(message=message, error_code=error_code)
        if self.not_found:
            return responses.ApiError(message=message, error_code=error_code)


class UserPopulateOptions(BaseModel):
    role: Union[bool, "RolesPopulateOptions"] = Field(False)
    account: Union[bool, "AccountPopulateOptions"] = Field(False)

    def build_pipeline(self) -> list[dict]:

        pipeline = []
        if self.role:
            role_pipeline = []
            if not self.role == True:
                role_pipeline = self.role.build_pipeline()

            pipeline.extend(aggregations.lookup_user_role(role_pipeline))

        if self.account:
            account_pipeline = []
            if not self.account == True:
                account_pipeline = self.account.build_pipeline()

            pipeline.extend(aggregations.lookup_user_account(account_pipeline))

        return pipeline


class AccountPopulateOptions(BaseModel):
    allowed_lessons: Union[bool, "PublishedLessonPopulateOptions"] = Field(False)
    allowed_categories: bool = Field(False)

    def build_pipeline(self) -> list[dict]:

        pipeline = []

        if self.allowed_lessons:
            lesson_pipeline = []
            if not self.allowed_lessons == True:
                lesson_pipeline = self.allowed_lessons.build_pipeline()

            pipeline.extend(
                aggregations.lookup_account_allowed_lessons(lesson_pipeline)
            )

        if self.allowed_categories:
            pipeline.append(aggregations.lookup_account_allowed_categories())

        return pipeline


class RolesPopulateOptions(BaseModel):
    categories: bool = Field(False)

    def build_pipeline(self) -> list[dict]:

        pipeline = []

        if self.categories:
            pipeline.append(aggregations.lookup_role_categories())

        return pipeline


class LessonPopulateOptions(BaseModel):
    categories: bool = Field(False)
    creator: Union[bool, "UserPopulateOptions"] = Field(False)

    def build_pipeline(self) -> list[dict]:

        pipeline = []

        if self.categories:
            pipeline.append(aggregations.lookup_lesson_categories())
        if self.creator:
            creator_pipeline = []

            if not self.creator == True:
                creator_pipeline = self.creator.build_pipeline()

            pipeline.extend(aggregations.lookup_lesson_creator(creator_pipeline))

        return pipeline


class PublishedLessonPopulateOptions(LessonPopulateOptions):
    current_editor: Union[bool, "UserPopulateOptions"] = Field(False)
    initial_editor: Union[bool, "UserPopulateOptions"] = Field(False)

    def build_pipeline(self) -> list[dict]:
        # to build the pipeline for "categories" and "creator" fields
        # we call the build_pipeline method of the parent class
        pipeline = super().build_pipeline()

        if self.current_editor:
            editor_pipeline = []

            if not self.current_editor == True:
                editor_pipeline = self.current_editor.build_pipeline()

            pipeline.extend(aggregations.lookup_lesson_current_editor(editor_pipeline))

        if self.initial_editor:
            editor_pipeline = []

            if not self.initial_editor == True:
                editor_pipeline = self.initial_editor.build_pipeline()

            pipeline.extend(aggregations.lookup_lesson_initial_editor(editor_pipeline))

        pipeline.append(
            aggregations.add_fields(
                edit_data={
                    "$cond": [f"${BaseLessonFields.mid_edit}", "$edit_data", None]
                }
            )
        )

        return pipeline


class DraftLessonPopulateOptions(LessonPopulateOptions):
    pass


class ArchivedLessonPopulateOptions(LessonPopulateOptions):
    archived_by: Union[bool, "UserPopulateOptions"] = Field(False)

    def build_pipeline(self) -> list[dict]:
        # to build the pipeline for "categories" and "creator" fields
        # we call the build_pipeline method of the parent class
        pipeline = super().build_pipeline()

        if self.archived_by:
            archived_by_pipeline = []

            if not self.archived_by == True:
                archived_by_pipeline = self.archived_by.build_pipeline()

            pipeline.extend(
                aggregations.lookup_lesson_archived_by(archived_by_pipeline)
            )

        return pipeline


class LessonReviewPopulateOptions(BaseModel):
    lesson: Union[bool, "PublishedLessonPopulateOptions"] = Field(False)
    user: Union[bool, "UserPopulateOptions"] = Field(False)

    @root_validator
    def validate_any_value(cls, values):
        if not any(values.values()):
            raise ValueError("At least one populate option must be true")
        return values

    def build_pipeline(self) -> list[dict]:

        pipeline = []

        if self.lesson:
            lesson_pipeline = []

            if not self.lesson == True:
                lesson_pipeline = self.lesson.build_pipeline()

            pipeline.extend(aggregations.lookup_lesson_review_lesson(lesson_pipeline))

        if self.user:
            user_pipeline = []

            if not self.user == True:
                user_pipeline = self.user.build_pipeline()

            pipeline.extend(aggregations.lookup_lesson_review_user(user_pipeline))

        return pipeline


UserPopulateOptions.update_forward_refs()
LessonPopulateOptions.update_forward_refs()
PublishedLessonPopulateOptions.update_forward_refs()
DraftLessonPopulateOptions.update_forward_refs()
AccountPopulateOptions.update_forward_refs()
LessonReviewPopulateOptions.update_forward_refs()
