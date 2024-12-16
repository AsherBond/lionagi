# Copyright (c) 2023 - 2024, HaiyangLi <quantocean.li at gmail dot com>
#
# SPDX-License-Identifier: Apache-2.0

from ..typing._pydantic import ConfigDict
from .base import BaseAutoModel

__all__ = ("SchemaModel",)


class SchemaModel(BaseAutoModel):

    model_config = ConfigDict(
        extra="forbid",
        validate_default=False,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )

    @classmethod
    def keys(cls) -> list[str]:
        """Get list of model field names.

        Returns:
            List of field names defined in model schema
        """
        return list(cls.model_fields.keys())
