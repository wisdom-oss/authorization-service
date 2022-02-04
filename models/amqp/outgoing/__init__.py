"""Package containing all outgoing response models"""
from pydantic import BaseModel, Field


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

    class Config:
        """Configuration for this Basic model"""

        orm_mode = True
        """Allow pydantic to read ORM classes into this model"""

        allow_population_by_field_name = True
        """Allow pydantic to populate field values by their actual python names and via the 
        aliases"""


class AMQPErrorResponse(BasicAMQPResponse):
    """A Response Model used for errors which occurred during the message handling"""

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
