"""Package containing all outgoing response models"""
from pydantic import Field

from models import BaseModel, shared


class BasicAMQPResponse(BaseModel):
    """
    A Basic Response Model for predefining some steps and properties of the models

    All other outgoing models shall be based on this class
    """

    status: str = Field(
        default='success',
        alias='status',
        title='Status of the message handling',
        description='This field will display the status of the message handling'
    )
    """Status of the message handling"""


class AMQPErrorResponse(BasicAMQPResponse):
    """A Response Model used for errors which occurred during the message handling"""

    status = 'error'
    """Since this is a error response the status will be error"""

    error: str = Field(
        default=...,
        alias='error',
        title='Short error name'
    )
    """A short error name specifying the type of error"""

    error_description: str = Field(
        default=None,
        alias='error_description',
        title='Error Description'
    )
    """A more accurate description of the error"""


class AMQPScopeResponse(shared.Scope, BasicAMQPResponse):
    """Data model for describing a scope which can be used in incoming/outgoing communication"""
    scope_id: int = Field(
        default=...,
        title='ID',
        description='Internally used id of the scope',
        alias='id'
    )
    """Internally used id of the scope"""
