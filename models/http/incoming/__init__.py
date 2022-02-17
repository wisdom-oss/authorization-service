# pylint: disable=too-few-public-methods, duplicate-code
"""Module containing the pydantic data models for incoming requests"""
from typing import Optional, Set

from pydantic import BaseModel, Field, SecretStr


class NewUserAccount(BaseModel):
    """New user account. This model only needs some basic information"""
    first_name: str = Field(
        default=...,
        title='First Name',
        description='The first name(s) of the newly created user',
        min_length=1,
        alias='firstName'
    )
    """First name(s) of the new user"""

    last_name: str = Field(
        default=...,
        title='Last name',
        description='The last name(s) of the newly created user',
        alias='lastName'
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

    scopes: Optional[str] = Field(
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


class UserUpdate(BaseModel):
    """A dataclass making all user account information of the new user optional"""
    first_name: Optional[str] = Field(
        default=None,
        title='First Name',
        description='The first name(s) of the newly created user',
        alias='firstName',
        min_length=1
    )
    """First name(s) of the new user"""

    last_name: Optional[str] = Field(
        default=None,
        title='Last name',
        alias='lastName',
        description='The last name(s) of the newly created user'
    )
    """Last name(s) of the new user"""

    username: Optional[str] = Field(
        default=None,
        title='Username'
    )
    """Username of the user"""

    password: Optional[SecretStr] = Field(
        default=None,
        title='Password',
        description='The password of the new user. This password is not retrievable via any '
                    'incoming or database query'
    )
    """Password of the new user"""

    active: Optional[bool] = Field(
        default=None,
        title='Status of the user',
        description='True for user enabled, False for user disabled'
    )
    """Status of the user (True == enabled)"""

    scopes: Optional[str] = Field(
        default=None,
        title='Scopes',
        description='The scopes this user may use'
    )
    """Scopes of the new users"""

    roles: Optional[Set[str]] = Field(
        default=None,
        title='Roles',
        description='The roles assigned to the user during the creation of the account'
    )
    """Names of the roles which shall be assigned to the new user"""

    class Config:
        """Configuration of this model"""
        allow_population_by_field_name = True
        allow_population_by_alias = True


class RoleUpdate(BaseModel):
    """Data model for the Roles"""
    role_name: Optional[str] = Field(
        default=None,
        title='Role Name',
        description='Name of the Role',
        alias='name'
    )
    """Name of the role"""

    role_description: Optional[str] = Field(
        default=None,
        title='Role Description',
        description='Text describing the role',
        alias='description'
    )
    """Textual description of the role"""

    role_scopes:Optional[str] = Field(
        default=None,
        title='Scopes',
        description='Scopes assigned to the role. These role are also granted explicitly to the '
                    'user',
        alias='scopes'
    )
    """Scopes assigned to the role"""

    class Config:
        """Configuration for this data model"""
        orm_mode = True
        """Allow the reading of properties via a orm model"""

        allow_population_by_field_name = True
        """Allow pydantic to use the field names to read the properties"""

        allow_population_by_alias = True
        """Allow pydantic to use the field aliases to read and assign properties"""


class Role(BaseModel):
    """Data model for the Role"""

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

    role_scopes: Optional[str] = Field(
        default=None,
        title='Scopes',
        description='Scopes assigned to the role. These role are also granted explicitly to the '
                    'user',
        alias='scopes'
    )
    """Scopes assigned to the role"""

    class Config:
        """Configuration for this pydantic model"""

        orm_mode = True
        """Allow the reading of properties via a orm model"""

        allow_population_by_field_name = True
        """Allow pydantic to use the field names to read the properties"""

        allow_population_by_alias = True
        """Allow pydantic to use the aliases to read properties"""
