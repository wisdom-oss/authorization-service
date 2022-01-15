"""SQLAlchemy-compatible object relational mappings for the used tables"""
from sqlalchemy import Column, Boolean, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .. import TableDeclarationBase

# Options for the foreign keys
FK_OPTIONS = {
    "onupdate": "CASCADE",
    "ondelete": "CASCADE"
}
"""Default options for the foreign key relations"""


class Role(TableDeclarationBase):
    """ORM mapping for the table containing the used roles"""

    __tablename__ = "roles"
    """Name of the table incoming the database"""

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    """Internal ID of the role"""

    role_name = Column(String(length=255), unique=True)
    """Name of the role (max. length 255, must be unique)"""

    role_description = Column(Text)
    """Textual description of the role"""

    scopes = relationship("Scope", secondary='role_scopes')
    """Scopes assigned to this role"""

    users = relationship("User", secondary='account_roles')
    """Users with the role"""


class Scope(TableDeclarationBase):
    """ORM for the table containing the available scopes"""

    __tablename__ = "scopes"
    """Name of the table incoming the database"""

    scope_id = Column(Integer, primary_key=True, autoincrement=True)
    """Internal id of the scope"""

    scope_name = Column(String(length=255), unique=True)
    """Name of the scope"""

    scope_description = Column(Text)
    """Textual description of the scope"""

    scope_value = Column(String(length=255), unique=True)
    """String used to identify the scope incoming OAuth2 scope strings"""


class AccessTokens(TableDeclarationBase):
    """ORM for the Authorization Tokens"""

    __tablename__ = "access_tokens"
    """Name of the table incoming the database"""

    token_id = Column(Integer, primary_key=True, autoincrement=True)
    """Internal id of the token"""

    token = Column(String(length=36, unique=True))
    """Actual token used incoming the Authorization header"""

    expires = Column(Integer, nullable=False)
    """Expiration date and time as UNIX Timestamp"""

    created = Column(Integer, nullable=False)
    """Creation date and time as UNIX Timestamp"""

    scopes = relationship("Scope", secondary='token_scopes')
    """Scopes associated with that token"""


class RefreshToken(TableDeclarationBase):
    """ORM for the refresh tokens"""

    __tablename__ = "refresh_tokens"
    """Name of the table incoming the database"""

    refresh_token_id = Column(Integer, primary_key=True, autoincrement=True)
    """Internal id of the refresh token"""

    refresh_token = Column(String(length=36), unique=True)
    """Actual refresh token"""

    expires = Column(Integer, nullable=False)
    """Expiration time and date as UNIX timestamp"""

    access_tokens = relationship("AccessToken", secondary='refresh_token_tokens')
    """Access tokens issued via this refresh token"""

    account = relationship("Account", secondary='account_refresh_tokens')
    """Account for this refresh_token"""


class Account(TableDeclarationBase):
    """ORM for the account table"""

    __tablename__ = "accounts"
    """Name of the table incoming the database"""

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    """Internal numeric account id"""

    first_name = Column(String(length=255), nullable=False)
    """First name(s) of the user associated to the account"""

    last_name = Column(String(length=255), nullable=False)
    """Last name(s) of the user associated to the account"""

    username = Column(String(length=510), nullable=False, unique=True)
    """Username for the account"""

    password = Column(Text, nullable=False)
    """Hashed password for the account"""

    is_active = Column(Boolean, default=True, nullable=False)
    """Status of the account"""

    scopes = relationship("Scope", secondary='account_scopes')
    """Scopes assigned to the account"""

    roles = relationship("Role", secondary='account_roles')
    """Roles assigned to the account"""

    tokens = relationship("Token", secondary='account_tokens')
    """Access tokens assigned to the account"""

    refresh_tokens = relationship("RefreshToken", secondary='account_refresh_tokens')
    """Refresh tokens assigned to the account"""


class RoleToScopes(TableDeclarationBase):
    """ORM for linking roles to the scopes they inherit"""

    __tablename__ = "role_scopes"
    """Name of the association table"""

    role_id = Column(Integer, ForeignKey('roles.role_id', **FK_OPTIONS))
    """ID of the role"""

    scope_id = Column(Integer, ForeignKey('scopes.scope_id', **FK_OPTIONS))
    """ID of the scope ofr this role"""


class TokenToScopes(TableDeclarationBase):
    """ORM for linking the issued tokens to the scopes they may use"""

    __tablename__ = "token_scopes"
    """Name of the association table"""

    token_id = Column(Integer, ForeignKey('access_tokens.token_id', **FK_OPTIONS))
    """ID of the Access Token"""

    scope_id = Column(Integer, ForeignKey('scopes.scope_id', **FK_OPTIONS))
    """ID of the scope for this token"""


class TokenToRefreshToken(TableDeclarationBase):
    """ORM for linking a token to a refresh token"""

    __tablename__ = "refresh_token_tokens"

    refresh_token_id = Column(Integer, ForeignKey('refresh_tokens.refresh_token_id', **FK_OPTIONS))
    """Internal ID of the refresh token"""

    access_token_id = Column(Integer, ForeignKey('access_tokens.token_id', **FK_OPTIONS))
    """Internal ID of the access token"""


class AccountToScope(TableDeclarationBase):
    """ORM for linking accounts to the scopes"""

    __tablename__ = "account_scopes"
    """Name of the association table"""

    account_id = Column(Integer, ForeignKey('accounts.account_id', **FK_OPTIONS))
    """Internal id of the account"""

    scope_id = Column(Integer, ForeignKey('scopes.scope_id', **FK_OPTIONS))
    """ID of the scope assigned to the account"""


class AccountToRoles(TableDeclarationBase):
    """ORM for linking accounts to the roles"""

    __tablename__ = "account_roles"
    """Name of the association table"""

    account_id = Column(Integer, ForeignKey('accounts.account_id', **FK_OPTIONS))
    """Internal ID of the account"""

    role_id = Column(Integer, ForeignKey('roles.role_id', **FK_OPTIONS))
    """ID of the role assigned to the account"""


class AccountToToken(TableDeclarationBase):
    """ORM for linking accounts to their tokens"""

    __tablename__ = "account_tokens"
    """Name of the association table"""

    account_id = Column(Integer, ForeignKey('accounts.account_id', **FK_OPTIONS))
    """Internal ID of the account"""

    token_id = Column(Integer, ForeignKey('access_tokens.token_id', **FK_OPTIONS))
    """ID of the token issued via this account"""


class AccountToRefreshTokens(TableDeclarationBase):
    """ORM for linking an account to their refresh tokens"""

    __tablename__ = "account_refresh_tokens"
    """Name of the association table"""

    account_id = Column(Integer, ForeignKey('accounts.account_id', **FK_OPTIONS))
    """Internal ID of the account"""

    refresh_token_id = Column(Integer, ForeignKey('refresh_tokens.refresh_token_id', **FK_OPTIONS))
    """ID of the refresh token for the account"""
