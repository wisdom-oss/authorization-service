"""Database module used for ORM descriptions of the used tables"""
import logging
import sys

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.ext.declarative
from sqlalchemy_utils import database_exists, create_database
from passlib import pwd

import models
import models.incoming
from . import crud
from .tables import Scope, TableDeclarationBase

__logger = logging.getLogger("DB")

# Read the service configuration to be able to set the database connection
__settings = models.ServiceSettings()
# Create a new (private) database engine
__engine = create_engine(
    url=__settings.database_dsn,
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


def _engine() -> Engine:
    """Get the raw database engine"""
    return __engine


def __generate_root_user(__db_session: DatabaseSession = next(session())):
    """Generate a new root user with the user id of 0 and the admin and me scope"""
    # Create the new user object
    _root_user = models.incoming.NewUserAccount(
        first_name='System',
        last_name='Administrator',
        username='root',
        password=str(pwd.genword(length=32, charset='ascii_72')),
        scopes='admin me'
    )
    __logger.info(
        'Generated "root" user with the following password: %s',
        _root_user.password.get_secret_value()
    )
    # Insert the user into the database
    return crud.add_user(_root_user, __db_session)


def __generate_scopes(__db_session: DatabaseSession = next(session())):
    """Create the admin and me scope to enable a basic configuration"""
    # Create a new ORM object for the Admin scope
    __admin_scope = Scope(
        scope_name='Administrator',
        scope_description='This scope allows the full administration of any aspect in this system.',
        scope_value="admin"
    )
    # Insert it into the database
    __db_session.add(__admin_scope)
    __db_session.commit()

    # Create a new ORM object for the "Me" scope
    __me_scope = Scope(
        scope_name='Read and write account details',
        scope_description='This scope allows the reading of all account data and allows changing '
                          'the accounts password',
        scope_value="me"
    )
    # Insert it into the database
    __db_session.add(__me_scope)
    __db_session.commit()


def initialise_databases():
    """Check if the database exists on the specified server and all tables are present"""
    if not database_exists(__settings.database_dsn):
        __logger.warning("The specified database does not exist on the server. The service will "
                         "now try to create the database and all tables needed for this service")
        # Try creating the database
        create_database(__settings.database_dsn)
        if database_exists(__settings.database_dsn):
            __logger.info("SUCCESS: The database was created successfully")
            TableDeclarationBase.metadata.create_all(bind=__engine)
            # Create some initial scopes (admin, me)
            __generate_scopes()
            __logger.info('SUCCESS: The initial scopes ("admin", "me") were created')
            # Generate an initial root user
            __generate_root_user()
            __logger.info('SUCCESS: The initial root user was created in the database')
        else:
            __logger.error("The database was not created due to an unknown error")
            sys.exit(1)
    else:
        TableDeclarationBase.metadata.create_all(bind=__engine)
