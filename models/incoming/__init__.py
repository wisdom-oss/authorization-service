"""Module containing the pydantic data models for incoming requests"""
from typing import List, Optional, Set

from pydantic import BaseModel, Field, SecretStr
from passlib import pwd

# pylint: disable=too-few-public-methods


class NewUserAccount(BaseModel):
    """New user account. This model only needs some basic information"""
    first_name: str = Field(
        default=...,
        title='First Name',
        description='The first name(s) of the newly created user',
        min_length=1
    )
    """First name(s) of the new user"""

    last_name: str = Field(
        default=...,
        title='Last name',
        description='The last name(s) of the newly created user'
    )
    """Last name(s) of the new user"""

    username: str = Field(
        default=...,
        title='Username'
    )
    """Username of the user"""

    password: SecretStr = Field(
        default=...,
        title='Password',
        description='The password of the new user. This password is not retrievable via any '
                    'incoming or database query'
    )
    """Password of the new user"""

    scopes: str = Field(
        default='me',
        title='Scopes',
        description='The scopes this user may use'
    )
    """Scopes of the new users"""

    roles: Optional[Set[str]] = Field(
        default={},
        title='Roles',
        description='The roles assigned to the user during the creation of the account'
    )
    """Names of the roles which shall be assigned to the new user"""

    class Config:
        """Configuration of this model"""
        allow_population_by_field_name = True
        allow_population_by_alias = True


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

    class Config:
        """Configuration of this model"""
        allow_population_by_field_name = True
        allow_population_by_alias = True
