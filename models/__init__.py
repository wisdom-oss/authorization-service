"""Module containing the data models for validating requests and responses as well as enabling
the settings"""
import pydantic

# pylint: disable=too-few-public-methods


class BaseModel(pydantic.BaseModel):
    """A basic data model containing a configuration which will be inherited into other models"""

    class Config:
        """The basic configuration for every model"""

        arbitrary_types_allowed = True
        """Allow arbitrary types in typing"""

        allow_population_by_field_name = True
        """Allow pydantic to populate fields by their name and not alias during parsing of 
        objects, raw input or ORMs"""
