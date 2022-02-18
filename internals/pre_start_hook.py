"""A simple script which uses the installed wait-for-it program to await the services needed in
this service"""
import subprocess
import sys
import logging

from pydantic import ValidationError
from sqlalchemy_utils import database_exists, create_database
from passlib import pwd

from models import ServiceSettings
from database import session, crud, engine
from database.tables import Account, Scope, TableDeclarationBase as Base
from models.http.incoming import NewUserAccount

logging.basicConfig(
    level=logging.INFO
)

__logger = logging.getLogger('PRE-START-HOOK')

if __name__ == '__main__':
    try:
        # Read the settings
        __settings = ServiceSettings()
    except ValidationError as e:
        __logger.error('Unable to parse the settings from the environment variables', exc_info=e)
        sys.exit(1)
    # Resolve the name of the needed services
    __service_registry = __settings.service_registry_host
    __database_host = __settings.database_dsn.host
    __database_port = 3306 if __settings.database_dsn.port is None else __settings.database_dsn.port
    __amqp_host = __settings.amqp_dsn.host
    __amqp_port = 5672 if __settings.amqp_dsn.port is None else __settings.amqp_dsn.port
    __command = 'wait-for-it {}:{} -s -q -t 0'
    # First wait for the service registry to come available
    __logger.info('Waiting for the service registry to come online')
    subprocess.run(__command.format(__service_registry, 8761), shell=True)
    # Wait for the database to be available
    __logger.info('Waiting for the database to come online')
    subprocess.run(__command.format(__database_host, __database_port), shell=True)
    # Wait for the message broker to be available
    __logger.info('Waiting for the message broker to come online')
    subprocess.run(__command.format(__amqp_host, __amqp_port), shell=True)
    # Since all needed services are online continue with a check of the database
    _db_session = next(session())
    if not database_exists(__settings.database_dsn):
        __logger.warning("The needed database was not found on the server")
        __logger.info('Creating the necessary database and tables')
        create_database(__settings.database_dsn)
        Base.metadata.create_all(bind=engine())
        __logger.info(
            'Since there was no database present, a root user with all privileges will '
            'now be generated'
        )
        # Check if the "admin" scope was not already created
        if crud.get_scope_by_value("admin", _db_session) is None:
            __logger.info('Creating the "admin" scope in the system')
            _admin_scope = Scope(
                scope_name='Administrator',
                scope_description='This scope allows the full access to all services and allows '
                                  'the management of the authorization service'
            )
            crud.add_to_database(_admin_scope, _db_session)
            __logger.info('Created the "admin" scope in the system')
        if crud.get_scope_by_value("me", _db_session) is None:
            _me_scope = Scope(
                scope_name='Read and write account details',
                scope_description='This scope allows the reading all account data and the '
                                  'possibility to change the password',
                scope_value='me'
            )
            crud.add_to_database(_me_scope, _db_session)
        # Now check if a user has not already been created
        if len(crud.get_all(Account, _db_session)) == 0:
            __logger.info(
                'Since no accounts were found in the account tables, a root user will '
                'now be created'
            )
            _username = str(pwd.genword(length=8))
            _password = str(pwd.genword(length=32, charset='ascii_72'))
            _root_user = NewUserAccount(
                first_name='Administrator',
                last_name='Administrator',
                username=_username,
                password=_password,
                scopes='admin me'
            )
            crud.add_user(_root_user, _db_session)
            __logger.info('Generated the root user with the following login data')
            __logger.info('Username: {}', _username)
            __logger.info('Password: {}', _password)
            __logger.info(
                'Please save the username and password since it will only displayed '
                'this one time.'
            )
    else:
        _user_list = crud.get_all(Account, _db_session)
        user_with_admin_found = False
        for user in _user_list:
            for scope in user.scopes:
                if scope.scope_name == "admin" and user.is_active:
                    user_with_admin_found = True
                    break
            if user_with_admin_found:
                break
        if not user_with_admin_found:
            __logger.warning(
                'There was no user identified which has an administrative access to the system. '
                'Therefore the authorization service is unmanageable. Please check if you '
                'accidentally disabled an administrators account'
            )
