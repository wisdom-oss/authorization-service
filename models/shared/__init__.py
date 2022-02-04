"""Package containing the data models which are shared throughout the application and access
methods"""
from typing import Optional

from pydantic import Field

from models import BaseModel


class TokenIntrospectionResult(BaseModel):
    """Pydantic data model for a token introspection response"""

    active: bool = Field(
        default=...,
        alias='active',
        title='Status of the presented token',
        description='The value of this is "true" if the token may be used for authorizing on the '
                    'server'
    )
    """Status of the token (true if is active and not revoked)"""

    scopes: Optional[str] = Field(
        default=None,
        alias='scope',
        title='OAuth2.0 Scopes',
        description='Scopes this token was associated with'
    )
    """Scopes this token was associated with"""

    username: Optional[str] = Field(
        default=None,
        alias='username',
        description='Owner of the token'
    )
    """Username identifying the owner of the token"""

    token_type: Optional[str] = Field(
        default=None,
        alias='token_type',
        description='Type of the token (either access_token or refresh_token)'
    )
    """Type of the token (either access_token or refresh_token)"""

    exp: Optional[int] = Field(
        default=None,
        alias='exp',
        description='UNIX timestamp of the expiry time'
    )
    """UNIX timestamp of expire time and date"""

    iat: Optional[int] = Field(
        default=None,
        alias='iat',
        description='UNIX timestamp indicating the creation time of the token'
    )


class Scope(BaseModel):
    # pylint: disable=R0801
    """OAuth2 Scope"""
    scope_name: str = Field(
        default=...,
        title='Name',
        description='The name of the scope given by the creator',
        alias='name'
    )
    """Name of the scope"""

    scope_description: str = Field(
        default='',
        title='Description',
        description='Textual description of the scope. This may contain hint as to what this '
                    'scope may be used for',
        alias='description'
    )
    """Textual description of the scope"""

    scope_value: str = Field(
        default=...,
        title='Value',
        description='The value represents the scope in a OAuth2 scope string',
        alias='value'
    )
    """OAuth2 scope string value identifying the scope"""


class ScopeUpdate(BaseModel):
    # pylint: disable=R0801
    """OAuth2 Scope"""
    scope_name: Optional[str] = Field(
        default=None,
        title='Name',
        description='The name of the scope given by the creator',
        alias='name'
    )
    """Name of the scope"""

    scope_description: Optional[str] = Field(
        default=None,
        title='Description',
        description='Textual description of the scope. This may contain hint as to what this '
                    'scope may be used for',
        alias='description'
    )
    """Textual description of the scope"""

    scope_value: Optional[str] = Field(
        default=None,
        title='Value',
        description='The value represents the scope in a OAuth2 scope string',
        alias='value'
    )
    """OAuth2 scope string value identifying the scope"""
