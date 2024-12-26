from enum import Enum

from .request_response_model import (
    ACTION_REQUESTS_FIELD,
    ACTION_RESPONSES_FIELD,
)
from .utils import ACTION_REQUIRED_FIELD, ARGUMENTS_FIELD, FUNCTION_FIELD

__all__ = (
    "ActionFieldModels",
    "ACTION_REQUESTS_FIELD",
    "ACTION_RESPONSES_FIELD",
    "FUNCTION_FIELD",
    "ARGUMENTS_FIELD",
    "ACTION_REQUIRED_FIELD",
)


class ActionFieldModels(Enum):
    ACTION_REQUESTS = ACTION_REQUESTS_FIELD
    ACTION_RESPONSES = ACTION_RESPONSES_FIELD
    ACTION_REQUIRED = ACTION_REQUIRED_FIELD
    FUNCTION = FUNCTION_FIELD
    ARGUMENTS = ARGUMENTS_FIELD
