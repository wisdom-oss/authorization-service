"""Package for describing the incoming amqp messages"""
from typing import Literal, Union

from pydantic import Field

import models.shared
from models import BaseModel
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


class AMQPCreateScopeRequest(models.shared.Scope):
    """A data model describing the amqp payload which needs to be sent"""

    action = Literal[AMQPActions.ADD_SCOPE]
    """The action which shall be executed"""


class AMQPUpdateScopeRequest(models.shared.ScopeUpdate):

    action = Literal[AMQPActions.EDIT_SCOPE]
    """The action which shall be executed"""

    scope_id = Field(
        default=...,
        alias='scopeID',
        title='Internal Scope ID',
        description='The ID of the scope that shall be modified'
    )


class IncomingAMQPRequest(BaseModel):
    """
    A data model for incoming AMQP messages
    """

    payload: Union[AMQPValidateTokenRequest, AMQPCreateScopeRequest] = Field(
        default=..., discriminator='action'
    )
