"""Database module used for ORM descriptions of the used tables"""
import logging
import sys
from pathlib import Path

import ujson
from pydantic import ValidationError
from sqlalchemy import create_engine

import database.crud
import models.requests
from configuration import DatabaseConfiguration

__logger = logging.getLogger("DB")
# Read the service configuration to be able to set the database connection
try:
    __settings = DatabaseConfiguration()
except ValidationError as error:
    logging.error("The configuration for the database connection could not be read")
    sys.exit(3)

engine = create_engine(url=__settings.dsn, pool_recycle=120)
