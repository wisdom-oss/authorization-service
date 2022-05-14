import asyncio
import logging
import multiprocessing
import sys
import typing

import py_eureka_client.eureka_client
import pydantic

import settings
import tools


_service_settings = settings.ServiceSettings()

# %% Configuration Variables
bind = f"0.0.0.0:{_service_settings.http_port}"
workers = multiprocessing.cpu_count() * 2 + 1
limit_request_line = 0
limit_request_fields = 0
limit_request_field_size = 0
max_requests = 10
max_requests_jitter = 10
worker_class = "gevent"

# %% Common Objects
_service_registry_client: typing.Optional[py_eureka_client.eureka_client.EurekaClient] = None


# %% Events
def on_starting(server):
    # Try to read the settings for connecting to the service registry
    try:
        _registry_settings = settings.ServiceRegistrySettings()
    except pydantic.ValidationError as e:
        logging.critical(
            "Unable to read the settings for connecting to the service registry", exc_info=e
        )
        sys.exit(1)
    # Try to read the settings for connecting to the database
    try:
        _database_settings = settings.DatabaseSettings()
    except pydantic.ValidationError as e:
        logging.critical("Unable to read the settings for connecting to the database", exc_info=e)
        sys.exit(1)
    # Check the connectivity to the service registry
    _registry_reachable = asyncio.run(
        tools.is_host_available(_registry_settings.host, _registry_settings.port)
    )
    if not _registry_reachable:
        logging.error(
            f"The service registry is currently not reachable on {_registry_settings.host}:"
            f"{_registry_settings.port}"
        )
        sys.exit(2)
    # Now access the service registry client and create one
    global _service_registry_client
    _service_registry_client = py_eureka_client.eureka_client.EurekaClient(
        eureka_server=f"http://{_registry_settings.host}:{_registry_settings.port}/",
        app_name=_service_settings.name,
        instance_port=_service_settings.http_port,
        should_register=True,
        should_discover=True,
        renewal_interval_in_secs=5,
        duration_in_secs=30,
    )
    _service_registry_client.start()
    _service_registry_client.status_update("STARTING")
    # TODO: Check if the necessary scopes and at least one user is present in the database


def when_ready(server):
    _service_registry_client.status_update("UP")


def on_exit(server):
    _service_registry_client.stop()
