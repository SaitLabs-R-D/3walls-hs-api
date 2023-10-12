from .lessons import (
    LessonPart,
    LessonScreen,
    DraftLessons,
    PublishedLessons,
    ArchiveLessons,
    LessonEdit,
    ScreensTypes,
)
from .categories import Categories
from .lessons_reviews import (
    LessonsReviews,
    RatingNames,
    Positions,
    Ratings,
    ReviewrInfo,
)
from .users import Users
from .accounts import Accounts
from .roles import (
    Roles,
    RolesInternalNames,
    Actions,
    Resources,
    Permissions,
    DynamicSources,
)
from .site_help import SiteHelp, SiteHelpCategories

from .common import DBModel, add_update_at_to_update
from typing import Type

__models__: list[Type[DBModel]] = [
    DraftLessons,
    PublishedLessons,
    ArchiveLessons,
    LessonsReviews,
    Categories,
    Users,
    Accounts,
    Roles,
    SiteHelp,
    SiteHelpCategories,
]
