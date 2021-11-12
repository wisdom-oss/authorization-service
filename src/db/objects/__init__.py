from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .. import TableBase


class Role(TableBase):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String, unique=True)
    role_description = Column(Text)

    users = relationship("UserRole", back_populates="role")
    scopes = relationship("RoleScope", back_populates="role")


class Scope(TableBase):
    __tablename__ = "scopes"

    scope_id = Column(Integer, primary_key=True)
    scope_name = Column(String(length=200), unique=True)
    scope_description = Column(Text)
    scope_value = Column(String(length=150), unique=True)

    users = relationship("UserScope", back_populates="scope")
    roles = relationship("RoleScope", back_populates="scope")


class RoleScope(TableBase):
    __tablename__ = "role_scopes"
    mapping_id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"))
    scope_id = Column(Integer, ForeignKey("scopes.scope_id"))

    role = relationship("Role", back_populates="scopes")
    scope = relationship("Scope", back_populates="roles")


class TokenScope(TableBase):
    __tablename__ = "token_scopes"

    mapping_id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.token_id"))
    scope_id = Column(Integer, ForeignKey("scopes.scope_id"))

    token = relationship("Token", back_populates="scopes")


class Token(TableBase):
    __tablename__ = "tokens"

    token_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    token = Column(Text, unique=True)
    expires = Column(Integer, nullable=False)
    created = Column(Integer, nullable=False)

    scopes = relationship("TokenScope", back_populates="token")
    user = relationship("UserToken", back_populates="token")
    refresh_token = relationship("RefreshToken", back_populates="access_token")


class UserScope(TableBase):
    __tablename__ = "user_scopes"
    """Name of the MySQL/MariaDB table in the database specified in the connection string"""

    mapping_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    scope_id = Column(Integer, ForeignKey("scopes.scope_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))

    user = relationship("User", back_populates="scopes")
    scope = relationship("Scope", back_populates="users")


class UserRole(TableBase):
    __tablename__ = "user_roles"
    """Name of the MySQL/MariaDB table in the database specified in the connection string"""

    mapping_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    role_id = Column(Integer, ForeignKey("roles.role_id"))

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class UserToken(TableBase):
    __tablename__ = "user_tokens"
    """Name of the MySQL/MariaDB table in the database specified in the connection string"""

    mapping_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    token_id = Column(Integer, ForeignKey("tokens.token_id"))

    user = relationship("User", back_populates="tokens")
    token = relationship("Token", back_populates="user")


class User(TableBase):
    __tablename__ = "users"
    """Name of the MySQL/MariaDB table in the database specified in the connection string"""

    # Columns in the table. This needs to match exactly the table definition.
    user_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    first_name = Column(String(length=100), unique=True, nullable=False)
    last_name = Column(String(length=100), unique=True, nullable=False)
    username = Column(String(length=200), unique=True, nullable=False)
    password = Column(Text, unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    scopes = relationship("UserScope", back_populates="user")
    roles = relationship("UserRole", back_populates="user")
    tokens = relationship("UserToken", back_populates="user")


class RefreshToken(TableBase):
    __tablename__ = "refresh_tokens"

    refresh_token_id = Column(Integer, primary_key=True)
    refresh_token = Column(Text, unique=True)
    for_token = Column(Integer, ForeignKey('tokens.token_id'))
    expires = Column(Integer)

    access_token = relationship("Token", back_populates="refresh_token")