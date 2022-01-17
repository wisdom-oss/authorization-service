"""Module containing the routes and actions run when requesting a specific route"""
import logging
from typing import Optional

from fastapi import FastAPI as fastapi_application
from fastapi import Request
from fastapi.responses import UJSONResponse
from py_eureka_client.eureka_client import EurekaClient

import database
from exceptions import AuthorizationException
from models import ServiceSettings

auth_service_rest = fastapi_application()
"""Main API application for this service"""

# Create a logger for the API and its routes
__logger = logging.getLogger('API')
# Get the service settings
__settings = ServiceSettings()
# Create a service registry client
__service_registry_client: Optional[EurekaClient] = None


# == Event handlers == #
@auth_service_rest.on_event('startup')
def api_startup():
    """Event handler for the startup.

    The code will be executed before any HTTP incoming will be accepted
    """
    # Get a logger for this event
    __log = logging.getLogger('API.startup')
    # Enable the global usage of the service settings and the service registry client
    global __settings, __service_registry_client
    # Create a new service registry client
    __service_registry_client = EurekaClient(
        eureka_server=__settings.service_registry_url,
        app_name='wisdom-oss_authorization-service',
        instance_port=5000,
        should_register=True,
        should_discover=False,
        renewal_interval_in_secs=5,
        duration_in_secs=10
    )
    # Start the registry client
    __service_registry_client.start()
    # Set the status of this service to starting to disallow routing to them
    __service_registry_client.status_update('STARTING')
    # Initialize the database models and connections and check for any errors in the database tables
    database.initialise_databases()
    # Inform the service registry of the new server status
    __service_registry_client.status_update('UP')


@auth_service_rest.on_event('shutdown')
def api_shutdown():
    """Event handler for the shutdown process of the application"""
    # Get a logger for this event
    __log = logging.getLogger('API.startup')
    # Enable the global usage of the registry client
    global __service_registry_client
    # Stop the client and deregister the service
    __service_registry_client.stop()


# == Exception handlers ==
@auth_service_rest.exception_handler(AuthorizationException)
async def handle_authorization_exception(
        _request: Request,
        e: AuthorizationException
) -> UJSONResponse:
    """Handle the Authorization exception

    This handler will set the error information according to the data present in the exception.
    Furthermore, the optional data will be passed in the `WWW-Authenticate` header.

    :param _request: The request in which the exception occurred in
    :param e: The Authorization Exception
    :return: A UJSON response
    """
    return UJSONResponse(
        status_code=e.http_status_code,
        content={
            "error": e.short_error,
            "error_description": e.error_description
        },
        headers={
            'WWW-Authenticate': f'Bearer {e.optional_data}'.strip()
        }
    )
