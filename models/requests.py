import typing
import pydantic

from models import BaseModel as __BaseModel


class AccountUpdateInformation(__BaseModel):
    first_name: typing.Optional[str] = pydantic.Field(default=None, alias="firstName")
    """The first name of the user who is the owner of the account"""

    last_name: typing.Optional[str] = pydantic.Field(default=None, alias="lastName")
    """The last name of the user who is the owner of the account"""

    username: typing.Optional[str] = pydantic.Field(default=None)
    """The username of the account"""

    keep_old_scopes: typing.Optional[bool] = pydantic.Field(default=True, alias="keepScopes")
    """Indicator for keeping the current scopes of the user"""

    scopes: typing.Optional[list[typing.Union[str, int]]] = pydantic.Field(
        default=None, alias="scopes"
    )
    """The new scopes if the current shall be replaced"""

    password: typing.Optional[pydantic.SecretStr] = pydantic.Field(default=None, alias="password")
    """The new password for this account"""


class AccountCreationInformation(__BaseModel):
    first_name: str = pydantic.Field(default=..., alias="firstName")
    """The first name of the user who is the owner of the account"""

    last_name: str = pydantic.Field(default=..., alias="lastName")
    """The last name of the user who is the owner of the account"""

    username: str = pydantic.Field(default=...)
    """The username of the account"""

    scopes: list[typing.Union[str, int]] = pydantic.Field(default=..., alias="scopes")
    """The new scopes if the current shall be replaced"""

    password: pydantic.SecretStr = pydantic.Field(default=..., alias="password")
    """The new password for this account"""


class ScopeUpdateData(__BaseModel):
    name: typing.Optional[str] = pydantic.Field(default=...)
    """The name of the scope"""

    description: typing.Optional[str] = pydantic.Field(default=...)
    """The description of the scope"""


class ScopeCreationData(__BaseModel):
    name: str = pydantic.Field(default=...)
    """The name of the scope"""

    description: str = pydantic.Field(default=...)
    """The description of the scope"""

    scope_string_value: str = pydantic.Field(default=...)
    """The value by which the scope is identifiable in a scope string"""
