"""Database module used for ORM descriptions of the used tables"""
import logging
import sys

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database

from models import ServiceSettings

# Logger the main module
from models.request import NewUserAccount

__logger = logging.getLogger("DB")

# Read the service configuration to be able to set the database connection
__settings = ServiceSettings()
# Create a new (private) database engine
__engine = create_engine(
    url=__settings.database_dsn,
    # Recreate the connection every 120 seconds. This is used to counter the forced disconnects
    # done by MariaDB servers
    pool_recycle=120
)
# Create a public session maker to be used as type hint and yielded object
DatabaseSession = sessionmaker(autoflush=False, autocommit=False, bind=__engine)

# Create a public TableBase used to set up the orm models later on
TableDeclarationBase = declarative_base()


def session() -> DatabaseSession:
    """Get an opened session for usage in the api dependencies"""
    __session = DatabaseSession()
    try:
        yield __session
    finally:
        __session.close()


def _engine() -> Engine:
    """Get the raw database engine"""
    return __engine


def __generate_root_user():
    """Generate a new root user with the user id of 0 and the admin and me scope"""
    # Create the new user object
    _root_user = NewUserAccount(
        first_name='System',
        last_name='Administrator',
        username='root'
    )
    __logger.info(
        'Generated "root" user with the following password: {}',
        _root_user.password.get_secret_value()
    )
    # Prepare the sql statement | TODO: Create ORM model for the users table


def initialise_databases():
    """Check if the database exists on the specified server and all tables are present"""
    if not database_exists(__settings.database_dsn):
        __logger.warning("The specified database does not exist on the server. The service will "
                         "now try to create the database and all tables needed for this service")
        # Try creating the database
        create_database(__settings.database_dsn)
        if database_exists(__settings):
            __logger.info("SUCCESS: The database was created successfully")
            # Generate an initial root user
            __generate_root_user()
        else:
            __logger.error("The database was not created due to an unknown error")
            sys.exit(1)
