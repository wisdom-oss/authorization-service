"""Datamodels for outgoing data"""
from typing import List, Optional, Set

from pydantic import BaseModel, Field

# pylint: disable=too-few-public-methods
from models import incoming


class Scope(incoming.Scope):
    """Data model for describing a scope which can be used in incoming/outgoing communication"""
    scope_id: int = Field(
        default=...,
        title='ID',
        description='Internally used id of the scope',
        alias='id'
    )
    """Internally used id of the scope"""

    class Config:
        """Configuration for this pydantic model"""

        orm_mode = True
        """Allow the reading of properties via a orm model"""

        allow_population_by_field_name = True
        """Allow pydantic to use the field names to read the properties"""

        allow_population_by_alias = True
        """Allow pydantic to use the aliases to read properties"""


class Role(BaseModel):
    """Data model for the Roles"""
    role_id: int = Field(
        default=...,
        title='Role ID',
        description='ID used to identify the role internally',
        alias='id'
    )
    """Internal id used to identify the role"""

    role_name: str = Field(
        default=...,
        title='Role Name',
        description='Name of the Role',
        alias='name'
    )
    """Name of the role"""

    role_description: str = Field(
        default='',
        title='Role Description',
        description='Text describing the role',
        alias='description'
    )
    """Textual description of the role"""

    role_scopes: Optional[Set[Scope]] = Field(
        default=None,
        title='Scopes',
        description='Scopes assigned to the role. These role are also granted explicitly to the '
                    'user',
        alias='scopes'
    )
    """Scopes assigned to the role"""


class UserAccount(BaseModel):
    """Datamodel describing the outgoing data about a user account"""
    account_id: int = Field(
        default=...,
        title='Account ID',
        description='Internally used id for each account',
        alias='id'
    )
    """Internal Account ID"""

    first_name: str = Field(
        default=...,
        title='First name(s)',
        description='First name(s) of the person associated to this account',
        alias='firstName'
    )
    """First name(s) of the person associated to this account"""

    last_name: str = Field(
        default=...,
        title='Last name(s)',
        description='Last name(s) of the person associated to this account',
        alias='lastName'
    )
    """Last name(s) of the person associated to this account"""

    username: str = Field(
        default=...,
        title='Username',
        description='Username for this account',
        alias='username'
    )
    """Username for this account"""

    is_active: bool = Field(
        default=...,
        title='Account Status',
        description='Boolean value showing if the account is active (true) or disabled (false)',
        alias='active'
    )
    """Account Status (True == active)"""

    scopes: List[Scope] = Field(
        default=[],
        title='Scopes',
        description='Scopes assigned to this user (also includes scopes from roles)',
        alias='scopes'
    )
    """All scopes assigned to this user"""

    roles: List[Role] = Field(
        default=[],
        title='Roles',
        description='All roles assigned to the user',
        alias='roles'
    )
    """Roles assigned to the user"""

    class Config:
        """Configuration for this data model"""
        orm_mode = True
        """Allow the reading of properties via a orm model"""

        allow_population_by_field_name = True
        """Allow pydantic to use the field names to read the properties"""


class TokenSet(BaseModel):
    """Data model for a token set after a successful authorization attempt"""

    access_token: str = Field(
        default=...,
        alias='accessToken',
        description='OAuth2 Bearer Token'
    )
    """OAuth2 Bearer Token"""

    token_type: str = Field(
        default="bearer",
        alias='tokenType',
        description='Type of the OAuth2 Token'
    )
    """Type of the OAuth2 Token"""

    expires_in: Optional[int] = Field(
        default=3600,
        description="Time to live of the token after it has been issued"
    )
    """TTL (time-to-live) of the token after it has been issued (Standard TTL: 3600)"""

    refresh_token: Optional[str] = Field(
        default=None,
        description='Refresh token which may be used to get a new access token'
    )
    """Refresh token which may be used to get a new access token"""

    scope: Optional[str] = Field(
        default="",
        description='Scopes of this token'
    )
    """Scope string for this token (optional if the token has the same scopes as requested)"""

    class Config:
        """Configuration for this pydantic model"""

        orm_mode = True
        """Allow the reading of properties via a orm model"""

        allow_population_by_field_name = True
        """Allow pydantic to use the field names to read the properties"""

        allow_population_by_alias = True
        """Allow pydantic to use the aliases to read properties"""


class TokenIntrospection(BaseModel):
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

    class Config:
        """Configuration for this pydantic model"""

        orm_mode = True
        """Allow the reading of properties via a orm model"""

        allow_population_by_field_name = True
        """Allow pydantic to use the field names to read the properties"""

        allow_population_by_alias = True
        """Allow pydantic to use the aliases to read properties"""
