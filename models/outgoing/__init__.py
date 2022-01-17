"""Datamodels for outgoing data"""
from typing import List, Optional, Set

from pydantic import BaseModel, Field


class Scope(BaseModel):
    """Data model for describing a scope which can be used in incoming/outgoing communication"""
    scope_id: int = Field(
        default=...,
        title='ID',
        description='Internally used id of the scope',
        alias='id'
    )
    """Internally used id of the scope"""

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

    class Config:
        """Configuration of this model"""
        allow_population_by_field_name = True
        allow_population_by_alias = True


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

    active: bool = Field(
        default=...,
        title='Account Status',
        description='Boolean value showing if the account is active (true) or disabled (false)',
        alias='is_active'
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
