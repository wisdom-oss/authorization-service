"""Database module used for ORM descriptions of the used tables"""
import logging
import sys

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from settings import DatabaseSettings
from . import crud
from .tables import Account, Scope, TableDeclarationBase

__logger = logging.getLogger("DB")
# Read the service configuration to be able to set the database connection
try:
    __settings = DatabaseSettings()
except ValidationError as error:
    logging.error('The settings for the database connection could not be read')
    sys.exit(3)
# Create a new (private) database engine
__engine = create_engine(
    url=__settings.dsn,
    # Recreate the connection every 120 seconds. This is used to counter the forced disconnects
    # done by MariaDB servers
    pool_recycle=120
)
# Create a public session maker to be used as type hint and yielded object
DatabaseSession = sessionmaker(autoflush=False, autocommit=False, bind=__engine)


def session() -> DatabaseSession:
    """Get an opened session for usage incoming the api dependencies"""
    __session = DatabaseSession()
    try:
        yield __session
    finally:
        __session.close()


def engine() -> Engine:
    """Get the raw database engine"""
    return __engine


def initialise_databases():
    """Check if the database exists on the specified server and all tables are present"""
    TableDeclarationBase.metadata.create_all(bind=__engine, checkfirst=True)
