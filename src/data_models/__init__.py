"""Module for describing the data models which will be used to work with the data and will be
used in responses and request parsing"""
from typing import List, Optional

from pydantic import BaseModel, Field


class Scope(BaseModel):
    id: int = Field(
        default=...,
        title='Internal Scope ID'
    )
    name: str = Field(
        default=...,
        title='Name of the Scope',
        description='This name should be unique throughout the wohle system to avoid any mix-ups '
                    'with scopes granting a different access to the system'
    )
    description: str = Field(
        default=...,
        title='Scope description'
    )


class Role(BaseModel):
    id: int = Field(
        default=...,
        title='Internal Role ID'
    )
    name: str = Field(
        default=...,
        title='Name of the role',
        description='This name should be unique throughout the whole system to avoid mix-ups with '
                    'roles which may have different scopes',
        alias='name'
    )
    description: str = Field(
        default=...,
        title='Description of the role. This may be displayed in the frontend'
    )
    scopes: Optional[List[Scope]] = Field(
        title='Scopes granted by the role'
    )


class User(BaseModel):
    id: int = Field(
        default=...,
        title='User ID',
        description='Internally used id for every account present in the system. This user id may '
                    'be used for updating users'
    )
    first_name: str = Field(
        default=...,
        title='First Name',
        description='The first name(s) of the user',
        alias='firstName'
    )
    last_name: str = Field(
        default=...,
        title='Last Name',
        description='The last name(s) of the user',
        alias='lastName'
    )
    last_login: Optional[int] = Field(
        title='Last Login (UNIX Timestamp)',
        description='The last login is determined by the last creation of a access token with the '
                    'user associated to. This may not be the last time the user has logged in via '
                    'the frontend, if there are external services connected via an token'
    )
    roles: Optional[List[Role]] = Field(
        title='Roles of the user',
        description='All roles assigned to the user. The scopes granted by the role will appear '
                    'here'
    )
    scopes: Optional[List[Scope]] = Field(
        title='Scopes of the user',
        description='All scopes explicitly to the user'
    )
