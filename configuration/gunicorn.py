import asyncio
import logging
import multiprocessing
import pathlib
import sys
import typing

import py_eureka_client.eureka_client
import pydantic
import sqlalchemy.schema
import ujson

import configuration
import database.crud
import database.helpers
import database.tables
import models.requests
import tools

_service_settings = configuration.ServiceConfiguration()

# %% Configuration Variables
bind = f"0.0.0.0:{_service_settings.http_port}"
workers = 1
limit_request_line = 0
limit_request_fields = 0
limit_request_field_size = 0
max_requests = 10
max_requests_jitter = 10
timeout = 0
preload_app = False
worker_class = "uvicorn.workers.UvicornWorker"

# %% Common Objects
_service_registry_client: typing.Optional[py_eureka_client.eureka_client.EurekaClient] = None


# %% Events
def on_starting(server):
    logging.basicConfig(
        format="[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    # Try to read the configuration for connecting to the service registry
    try:
        _registry_settings = configuration.ServiceRegistryConfiguration()
    except pydantic.ValidationError as e:
        logging.critical("Unable to read the configuration for connecting to the service registry", exc_info=e)
        sys.exit(1)
    # Try to read the configuration for connecting to the database
    try:
        _database_settings = configuration.DatabaseConfiguration()
    except pydantic.ValidationError as e:
        logging.critical("Unable to read the configuration for connecting to the database", exc_info=e)
        sys.exit(1)
    # Check the connectivity to the service registry
    _registry_reachable = asyncio.run(tools.is_host_available(_registry_settings.host, _registry_settings.port))
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
    if not database.engine.dialect.has_schema(database.engine, "authorization"):
        logging.info("Creating the 'authorization' schema in the specified database.")
        database.engine.execute(sqlalchemy.schema.CreateSchema("authorization"))
        database.tables.initialize()
        database.helpers.create_initial_data(pathlib.Path("./configuration/scopes.json").absolute())
    else:
        database.tables.initialize()
        required_scopes: list[dict] = ujson.load(open("./configuration/scopes.json"))
        for scope in required_scopes:
            if database.crud.get_scope(scope.get("scopeStringValue")) is None:
                _scope = models.requests.ScopeCreationData(
                    name=scope.get("name"),
                    description=scope.get("description"),
                    scope_string_value=scope.get("scopeStringValue"),
                )
                database.crud.store_new_scope(_scope)
        # Get the length of the user database entries
        users = database.crud.get_user_accounts()
        if len(users) == 0:
            logging.critical("No user present in the database. The service may not work as expected.")


def when_ready(server):
    _service_registry_client.status_update("UP")


def on_exit(server):
    _service_registry_client.stop()
