import datetime
import typing
import uuid

import passlib.hash
import pydantic

import models


class UserAccount(models.BaseModel):

    id: int = pydantic.Field(default=..., title="Internal Account ID")
    """Internal Account ID"""

    first_name: str = pydantic.Field(default=..., title="First Name")
    """The first name of the user who is the owner of the account"""

    last_name: str = pydantic.Field(default=..., title="Last Name")
    """The last name of the user who is the owner of the account"""

    username: str = pydantic.Field(default=..., title="Username")
    """The username of the account"""

    password: pydantic.SecretStr = pydantic.Field(default=..., title="Password")
    """The password of the account"""

    active: bool = pydantic.Field(default=..., title="Active Account")
    """Indicator if the account is active"""


class TokenSet(models.BaseModel):

    access_token: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
    """The access token used in the Bearer header"""

    access_token_type: str = pydantic.Field(default="bearer", alias="token_type")
    """The type of the access token"""

    expires_in: typing.Optional[int] = pydantic.Field(default=3600)
    """The TTL in seconds of the access token"""

    refresh_token: str = pydantic.Field(default=None)
    """The optional refresh token which may be used to generate a new token pair"""

    scopes: typing.Optional[typing.Union[str, list[str]]] = pydantic.Field(default="")
    """The scopes this token is valid for"""

    @pydantic.validator("scopes")
    def convert_scope_list_to_string(cls, v):
        if type(v) is list:
            return " ".join(v)
        elif type(v) is str:
            return v
        else:
            raise TypeError("The scope parameter only accepts lists or strings")

    @pydantic.validator("refresh_token", always=True)
    def generate_refresh_token(cls, v, values):
        if v is not None:
            return v
        access_token = str(uuid.uuid4())
        return passlib.hash.hex_sha512.hash(access_token)


class Scope(models.BaseModel):

    id: int = pydantic.Field(default=None)
    """The internal database id of the scope"""

    name: str = pydantic.Field(default=...)
    """The name of the scope"""

    description: str = pydantic.Field(default=...)
    """The description of the scope"""

    scope_string_value: str = pydantic.Field(default=...)
    """The value by which the scope is identifiable in a scope string"""


class TokenInformation(models.BaseModel):

    id: int = pydantic.Field(default=None)
    """The internal database id of the token"""

    value: pydantic.SecretStr = pydantic.Field(default=...)
    """The encoded value of the token"""

    active: bool = pydantic.Field(default=...)
    """The status of the token"""

    expires: datetime.datetime = pydantic.Field(default=...)
    """The time and date of expiration"""

    created: typing.Optional[datetime.datetime] = pydantic.Field(default=None)
    """The time and date on which the token has been created"""

    owner_id: int = pydantic.Field(default=...)
    """The id of the account this token is associated to"""
