"""Package for describing the incoming amqp messages"""
from typing import Literal, Union

from pydantic import BaseModel, Field

from models.enums import AMQPActions


class AMQPValidateTokenRequest(BaseModel):
    """
    A data model for validating a token request
    """

    action: Literal[AMQPActions.VALIDATE_TOKEN]
    """The action which shall be executed"""

    token: str = Field(
        default=...,
        alias='token',
        title='OAuth2.0 Token',
        description='The token which shall be validated in the system'
    )
    """The token which shall be validated"""

    scopes: str = Field(
        default=...,
        alias='scopes',
        title='OAuth2.0 Scopes',
        description='The scopes the token shall be checked against'
    )
    """The scopes which shall be tested for the token"""


class AMQPRevokeTokenRequest(BaseModel):
    """
    A data model for validating a token request
    """

    action: Literal[AMQPActions.REVOKE_TOKEN]
    """The action which shall be executed"""

    token: str = Field(
        default=...,
        alias='token',
        title='OAuth2.0 Token',
        description='The token which shall be validated in the system'
    )
    """The token which shall be revoked"""


class IncomingAMQPRequest(BaseModel):
    """
    A data model for incoming AMQP messages
    """

    payload: Union[AMQPValidateTokenRequest, AMQPRevokeTokenRequest] = Field(
        default=..., discriminator='action'
    )
