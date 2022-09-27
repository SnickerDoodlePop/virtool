from typing import Optional

from pydantic import BaseModel, constr, Field, validator
from virtool_core.models.label import Label

from virtool_core.models.validators import normalize_hex_color


class CreateLabelSchema(BaseModel):
    """
    Label fields for creating a new label.
    """

    name: constr(strip_whitespace=True, min_length=1) = Field(
        description="unique name for the label document"
    )
    color: constr(strip_whitespace=True) = Field(
        default="#A0AEC0", description="color of the label"
    )
    description: constr(strip_whitespace=True) = Field(
        default="", description="description of the document"
    )

    _ensure_color_is_normalized: classmethod = validator("color", allow_reuse=True)(
        normalize_hex_color
    )

    class Config:
        schema_extra = {
            "example": {
                "color": "#374151",
                "description": "dsRNA/binding protein",
                "name": "Binding protein",
            }
        }


class CreateLabelResponse(Label):
    class Config:
        schema_extra = {
            "example": {
                "color": "#374151",
                "count": 0,
                "description": "dsRNA/binding protein",
                "id": 23,
                "name": "Binding protein",
            }
        }


class UpdateLabelSchema(BaseModel):
    """
    Label fields for editing an existing label.
    """

    name: Optional[constr(strip_whitespace=True)] = Field(
        description="A short display name"
    )
    color: Optional[constr(strip_whitespace=True)] = Field(
        description="A hexadecimal color for the label"
    )
    description: Optional[constr(strip_whitespace=True)] = Field(
        description="A longer description for the label"
    )

    _ensure_color_is_normalized: classmethod = validator("color", allow_reuse=True)(
        normalize_hex_color
    )

    class Config:
        schema_extra = {
            "example": {
                "color": "#93C5FD",
                "description": "Field samples from 2022 harvest",
                "name": "Blueberry 2022",
            }
        }


class LabelResponse(Label):
    class Config:
        schema_extra = {
            "example": {
                "color": "#6B7280",
                "count": 0,
                "description": "dsRNA/Ab",
                "id": 22,
                "name": "Ab",
            }
        }


class GetLabelResponse(Label):
    class Config:
        schema_extra = {
            "example": [
                {
                    "color": "#6B7280",
                    "count": 0,
                    "description": "dsRNA/Ab",
                    "id": 22,
                    "name": "Ab",
                }
            ]
        }