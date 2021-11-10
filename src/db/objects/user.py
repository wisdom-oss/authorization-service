"""Module specifying the layout of the user table and other user related tables"""
from sqlalchemy import Column, Boolean, ForeignKey, String, Text, Integer
from sqlalchemy.orm import relationship

from .. import TableBase


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
    tokens = relationship("UserToken", back_populates="user")


class UserScope(TableBase):
    __tablename__ = "user_scopes"
    """Name of the MySQL/MariaDB table in the database specified in the connection string"""

    mapping_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    scope_id = Column(Integer, ForeignKey("scopes.scope_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))

    user = relationship("User", back_populates="scopes")
    scope = relationship("scope.Scope", back_populates="users")


class UserRole(TableBase):
    __tablename__ = "user_roles"
    """Name of the MySQL/MariaDB table in the database specified in the connection string"""

    mapping_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    role_id = Column(Integer, ForeignKey("roles.role_id"))

    user = relationship("User", back_populates="roles")
    role = relationship("role.Role", back_populates="users")


class UserToken(TableBase):
    __tablename__ = "user_roles"
    """Name of the MySQL/MariaDB table in the database specified in the connection string"""

    mapping_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    token_id = Column(Integer, ForeignKey("tokens.token_id"))

    user = relationship("User", back_populates="tokens")
    token = relationship("Token", back_populates="tokens")
