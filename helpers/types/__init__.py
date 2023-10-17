from enum import Enum
from .db import (
    QueryResults,
    InsertResults,
    UpdateResults,
    UserPopulateOptions,
    AccountPopulateOptions,
    PublishedLessonPopulateOptions,
    DraftLessonPopulateOptions,
    RolesPopulateOptions,
    ArchivedLessonPopulateOptions,
)
from .requests import (
    RequestWithUserId,
    RequestWithDraft,
    RequestWithFullUser,
    RequestWithPaginationAndFullUser,
    RequestWithPagination,
)


class PcPlatform(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MAC = "mac"

    def get_extansion(self) -> str:
        if self == PcPlatform.WINDOWS:
            return "exe"
        elif self == PcPlatform.MAC:
            return "dmg"
        elif self == PcPlatform.LINUX:
            return "AppImage"


class RediractsPaths(str, Enum):
    HOME = "/"
    LOGIN = "/login"


class Cookeys(str, Enum):
    ACCESS_TOKEN = "hs_access_token"


class CookiesExpiration(str, Enum):
    MFA_TOKEN = 60 * 5  # 5 minutes
    MAX = 2**31 - 1
    ACCESS_TOKEN = MAX
