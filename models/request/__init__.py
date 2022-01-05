"""Module containing the pydantic data models for incoming requests"""
from typing import List, Optional

from pydantic import BaseModel, Field, SecretStr
from passlib import pwd


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
        default=pwd.genword(length=32, charset='ascii_72'),
        title='Password',
        description='The password of the new user. If none is supplied a random password will be '
                    'generated. This password is not retrievable via any request or database query'
    )
    """Password of the new user. (Auto-generated if none is supplied)"""

    scopes: str = Field(
        default='me',
        title='Scopes',
        description='The scopes this user may use'
    )
    """Scopes of the new users"""

    roles: Optional[List[str]] = Field(
        default=[],
        title='Roles',
        description='The roles assigned to the user during the creation of the account'
    )
    """Roles of the new user"""
