from enum import Enum


class RedisKeyTypes(str, Enum):
    USER = "user"


class RedisKeyActions(str, Enum):
    PERMISSIONS = "pr"
    ACCESS_TOKEN = "at"
