"""A collection of tools used multiple times throughout this service"""
import asyncio
import logging
import sys
import time

import passlib.pwd
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from database import crud
from database.tables import Scope, Account, TableDeclarationBase
from models.http.incoming import NewUserAccount

_logger = logging.getLogger('TOOLS')


def resolve_log_level(level: str) -> int:
    """Resolve the logging level from a string

    This method will try to get the actual logging level from the logging package

    If no valid logging level is supplied this method will return the info level

    :param level: The name of the level which should be resolved
    :return: The logging level which may be used in the configuration of loggers
    """
    return getattr(logging, level.upper(), logging.INFO)


async def is_host_available(
        host: str,
        port: int,
        timeout: int = 10
) -> bool:
    """Check if the specified host is reachable on the specified port

    :param host: The hostname or ip address which shall be checked
    :param port: The port which shall be checked
    :param timeout: Max. duration of the check
    :return: A boolean indicating the status
    """
    _end_time = time.time() + timeout
    while time.time() < _end_time:
        try:
            # Try to open a connection to the specified host and port and wait a maximum time of five seconds
            _s_reader, _s_writer = await asyncio.wait_for(asyncio.open_connection(host, port),
                                                          timeout=5)
            # Close the stream writer again
            _s_writer.close()
            # Wait until the writer is closed
            await _s_writer.wait_closed()
            return True
        except:
            # Since the connection could not be opened wait 5 seconds before trying again
            await asyncio.sleep(5)
    return False


def create_minimal_database_content(engine: Engine, session: Session):
    """Create the admin and me scopes and create a root user for initializing the authorization
    service
    
    :param engine: The database engine via which the metadata is bound
    :param session: The database session which is used to insert the scopes and user
    """
    _logger.info('Initializing the database tables and inserting base data')
    # Initialize the ORM mappings
    TableDeclarationBase.metadata.create_all(bind=engine)
    # Check if the admin scope has not been created manually
    if crud.get_scope_by_value("admin", session) is None:
        _logger.info('Creating the "admin" scope')
        _admin_scope = Scope(
            scope_name='Authorization Administration',
            scope_description='This scope allows the administrative access to the authorization '
                              'service',
            scope_value='admin'
        )
        crud.add_to_database(_admin_scope, session)
        _logger.info('Created the "admin" scope in the database')
    # Check if the "me" scope has not been created manually
    if crud.get_scope_by_value("me", session) is None:
        _logger.info('Creating the "me" scope')
        _me_scope = Scope(
            scope_name='Account Access',
            scope_description='This scope allows the reading of all account data and the '
                              'possibility to change the account\'s password',
            scope_value='me'
        )
        crud.add_to_database(_me_scope, session)
        _logger.info('Created the "me" scope')
    # Check if any user has already been added to the system manually
    if len(crud.get_all(Account, session)) == 0:
        _logger.info('No accounts were created in the tables beforehand. Generating a root user')
        # Generate a random username
        _username = str(passlib.pwd.genword(length=8))
        # Generate a random password
        _password = str(passlib.pwd.genword(length=32, charset='ascii_72'))
        # Create the new user account
        _user = NewUserAccount(
            first_name='Administrator',
            last_name='Administrator',
            username=_username,
            password=_password,
            scopes='admin me'
        )
        # Add the user to the database
        crud.add_user(_user, session)
        _logger.info('Generated the new root user with the following login data')
        _logger.info('Username: %s', _username)
        _logger.info('Password: %s', _password)
        _logger.info(
            'Save the login data at a secure location. The login data will only be shown once')
    elif not database_contains_active_administrator(session):
        _logger.critical('There is no user with administrative access to the authorization '
                         'service. Therefore, no users/scopes/roles may be '
                         'added/modified/deleted.')
        sys.exit(7)


def database_contains_active_administrator(session: Session):
    """Check if the database contains at least one active administrator
    
    :param session:
    :return:
    """
    _users = crud.get_all(Account, session)
    user_with_admin_present = False
    for user in _users:
        for scope in user.scopes:
            if scope.scope_value == "admin" and user.is_active:
                user_with_admin_present = True
                break
        if user_with_admin_present:
            break
    return user_with_admin_present
