"""Module for describing the layout of the token related tables"""
from sqlalchemy import Column, Boolean, ForeignKey, String, Text, Integer
from sqlalchemy.orm import relationship

from .. import TableBase


class Token(TableBase):
    __tablename__ = "tokens"

    token_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    token = Column(Text, unique=True)
    expires = Column(Integer, nullable=False)
    created = Column(Integer, nullable=False)

    scopes = relationship("TokenScope", back_populates="token")
    user = relationship("user.UserToken", back_populates="token")


class TokenScope(TableBase):
    __tablename__ = "token_scopes"

    mapping_id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.token_id"))
    scope_id = Column(Integer, ForeignKey("scopes.scope_id"))

    token = relationship("Token", back_populates="scopes")
