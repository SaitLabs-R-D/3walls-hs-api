from enum import Enum
from .common import DBModel, MongoIndex
from pydantic import Field, BaseModel, root_validator
from typing import Union, Literal, Any, Optional
from helpers.fields import ObjectIdField


class RolesInternalNames(str, Enum):
    # must not be a part of a institution
    ADMIN = "admin"
    INSTATUTION_MANAGER = "institution_manager"
    # editor must be a part of a institution
    EDITOR = "editor"
    # viewer must be a part of a institution
    VIEWER = "viewer"
    # must not be a part of a institution
    GUEST = "guest"


class Roles(DBModel):
    categories: Union[list[ObjectIdField], list["Categories"]] = Field(
        default_factory=list
    )
    lessons: Union[list[ObjectIdField], list["PublishedLessons"]] = Field(
        default_factory=list
    )
    name: str = Field(...)
    internal_name: RolesInternalNames = Field(...)
    # for each collection that the role can access
    # create a new permission
    permissions: list["Permissions"] = Field(...)
    # This field is being used to check if the user can edit the role
    # or add it to a user, its happing in the permissions array
    managed_roles: Union[list[ObjectIdField], Literal["*"]] = Field(
        default_factory=list
    )
    require_account: bool = Field(True)
    # the lower the rank, the higher the role
    rank: int = Field(...)

    class Fields(str, Enum):
        id = "_id"
        name_ = "name"
        categories = "categories"
        lessons = "lessons"
        internal_name = "internal_name"
        description = "description"
        permissions = "permissions"
        managed_roles = "managed_roles"
        require_account = "require_account"

    @classmethod
    def get_indexes(cls) -> list[MongoIndex]:
        unique_internal_name = (
            MongoIndex(
                "unique_internal_name",
            )
            .add_field(cls.Fields.internal_name, 1)
            .set_unique()
        )

        unique_name = (
            MongoIndex(
                "unique_name",
            )
            .add_field(cls.Fields.name_, 1)
            .set_unique()
        )

        text_search = MongoIndex(
            "text_search",
        ).add_field(cls.Fields.name_, "text")

        return [unique_internal_name, unique_name, text_search]


class Permissions(BaseModel):
    resource: "Resources" = Field(...)
    actions: list["Actions"] = Field(...)
    # the filter will be applied on every action related to the collection
    filters: list["ResourcesFilter"] = Field(default_factory=list)


class ResourcesFilter(BaseModel):
    # if true, the filter will be added to the $or operator
    is_or: bool = Field(False)
    # if true, the filter will be added to the $and operator
    is_and: bool = Field(False)
    # To use nested filters, use the dot notation
    field: str = Field(...)
    # If you pass a wild card (*) and the action is UPDATE_LIMITES
    # the field will not be editable
    value: Any = Field(None)
    operator: "ResourcesFilterOperators" = Field(...)
    # if true, the value will be from the current user document
    # so it can only be a field from the user document
    dynamic: bool = Field(False)
    # if dynamic is true, this field will be used to get the value
    # from the dynamic_source document by using the [field] value
    dynamic_field: list[str] = Field(None)

    dynamic_source: Optional["DynamicSources"] = Field(None)

    apply_to: list["Actions"] = Field(
        default_factory=lambda: [action for action in Actions]
    )
    description: Optional[str] = Field(None)

    @root_validator
    def validate_dynamic(cls, values):
        if values.get("dynamic") and not values.get("dynamic_source"):
            raise ValueError("If dynamic is true, dynamic_source must be provided")

        return values

    class Fields(str, Enum):
        field = "field"
        value = "value"


class ResourcesFilterOperators(str, Enum):
    EQUAL = "$eq"
    NOT_EQUAL = "$ne"
    GREATER_THAN = "$gt"
    GREATER_THAN_OR_EQUAL = "$gte"
    LESS_THAN = "$lt"
    LESS_THAN_OR_EQUAL = "$lte"
    IN = "$in"
    NOT_IN = "$nin"
    EXISTS = "$exists"
    REGEX = "$regex"


class Resources(str, Enum):
    ROLES = "roles"
    USERS = "users"
    ACCOUNTS = "accounts"
    DRAFT_LESSONS = "draft_lessons"
    PUBLISHED_LESSONS = "published_lessons"
    ARCHIVED_LESSONS = "archived_lessons"
    CATEGORIES = "categories"
    REVIEWS = "reviews"
    SITE_HELP = "site_help"
    SITE_HELP_CATEGORIES = "site_help_categories"


class Actions(str, Enum):
    CREATE = "create"
    READ = "read"
    READ_MANY = "read_many"
    UPDATE = "update"
    DELETE = "delete"
    DUPPLICATE = "dupplicate"
    UPDATE_LIMITES = "update_limites"
    CREATE_LIMITES = "create_limites"
    READ_UPDATE_LIMITES = "read_update_limites"


class DynamicSources(str, Enum):
    CURRENT_USER = "current_user"


from .categories import Categories
from .lessons.published import PublishedLessons

Roles.update_forward_refs()
ResourcesFilter.update_forward_refs()
Permissions.update_forward_refs()
