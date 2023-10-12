from enum import Enum


class ErrorType(str, Enum):

    UNKNOWN_ERROR = "E0"
    FAILD_QUERY = "E1"
    VALIDATION_ERROR = "E2"
