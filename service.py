"""Spinup script for this service"""
import asyncio
import logging
import sys
from threading import Event

import pymysql.err
import sqlalchemy_utils as sql_utils
import uvicorn
from pydantic import ValidationError

import tools
from database import engine, session
from settings import *

_shutdown_event = Event()
_shutdown_event.clear()


if __name__ == '__main__':
    # Read the service settings
    _service_settings = ServiceSettings()
    # Configure the logging module
    logging.basicConfig(
        format='%(levelname)-8s | %(asctime)s | %(name)-25s | %(message)s',
        level=tools.resolve_log_level(_service_settings.log_level)
    )
    # Log a startup message
    logging.info(f'Starting the {_service_settings.name} service')
    logging.debug('Reading the settings for the Service Registry connection')
    try:
        _registry_settings = ServiceRegistrySettings()
    except ValidationError as error:
        logging.error('The settings for the Service Registry could not be read')
        sys.exit(2)
    logging.debug('Reading the settings for the database connection')
    try:
        _database_settings = DatabaseSettings()
    except ValidationError as error:
        logging.error('The settings for the database connection could not be read')
        sys.exit(3)
    # Check if the service registry is reachable
    logging.info('Checking the communication to the service registry')
    _registry_available = asyncio.run(
        tools.is_host_available(
            host=_registry_settings.host,
            port=_registry_settings.port
        )
    )
    if not _registry_available:
        logging.critical(
            'The service registry is not reachable. The service may not be reachable via the '
            'Gateway'
        )
        sys.exit(4)
    else:
        logging.info('SUCCESS: The service registry appears to be running')
    # Check if the database is reachable
    logging.info('Checking the communication to the database')
    _database_reachable = asyncio.run(
        tools.is_host_available(
            host=_database_settings.dsn.host,
            port=3306 if _database_settings.dsn.port is None else int(_database_settings.dsn.port)
        )
    )
    if not _database_reachable:
        logging.critical(
            'The database is not reachable. Since the database stores the necessary data the '
            'service cannot start'
        )
        sys.exit(5)
    else:
        logging.info('SUCCESS: The database appears to be running')
    # Check if the database exists
    if not sql_utils.database_exists(_database_settings.dsn):
        logging.warning('The specified database does not exist on the specified server')
        logging.info('Trying to create the specified database')
        try:
            sql_utils.create_database(_database_settings.dsn)
        except pymysql.err.ProgrammingError as e:
            logging.critical(
                'The database creation failed since the database was already created in the meantime'
            )
            sys.exit(6)
        # Try to create the missing tables
        tools.create_minimal_database_content(engine(), next(session()))
    else:
        logging.info('Found an existing database and existing tables. Checking the contents of '
                     'the tables')
        # Get a list of all users and check if there is any user with administrative access
        if not tools.database_contains_active_administrator(next(session())):
            logging.critical('There is no user with administrative access to the authorization '
                             'service. Therefore, no users/scopes/roles may be '
                             'added/modified/deleted.')
            sys.exit(8)
    uvicorn.run(**{
            "app": "api:auth_service_rest",
            "host": "0.0.0.0",
            "port": _service_settings.http_port,
            "log_level": "warning",
            "workers": 1
        })
