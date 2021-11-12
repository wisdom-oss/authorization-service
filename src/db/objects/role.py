"""Module for describing the layout of the scope related tables"""
from sqlalchemy import Column, Boolean, ForeignKey, String, Text, Integer
from sqlalchemy.orm import relationship

from .. import TableBase


class Role(TableBase):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String, unique=True)
    role_description = Column(Text)