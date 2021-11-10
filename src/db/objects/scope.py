"""Module for describing the layout of the scope related tables"""
from sqlalchemy import Column, Boolean, ForeignKey, String, Text, Integer
from sqlalchemy.orm import relationship

from .. import TableBase


class Scope(TableBase):
    __tablename__ = "scopes"

    scope_id = Column(Integer, primary_key=True)
    scope_name = Column(String(length=200), unique=True)
    scope_description = Column(Text)
    scope_value = Column(String(length=150), unique=True)

    users = relationship("user.User", back_populates="scope")
