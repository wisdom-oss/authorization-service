# pylint: disable=too-few-public-methods
"""Package describing a basic data model to allow"""
from pydantic import BaseModel, Field


class AMQPBaseModel(BaseModel):
    """A preconfigured class for all AMQP models which also contains some necessary information
    for later operations"""

    action: str = Field(
        default=...,
        title='Action',
        description='Which action shall be executed on retrieval of the message',
        alias='retrieval_action'
    )
    """The action which shall be executed"""

    correlation_id: str = Field(
        default=...,
        title='Correlation ID',
        description='The correlation id the request contained. This shall be used to identify the '
                    'requests later on',
    )
    """AMQP Correlation ID sent with the original request"""

    class Config:
        """Model configuration which is inherited by other models"""

        use_enum_values = True
        """If a enumeration is used as datatype set the value to the field and not the enum"""

        allow_population_by_field_name = True
        """Allow pydantic to assign a field by its name as well as the alias"""

        smart_union = True
        """Let pydantic check all types noted in a union before setting the type"""