import asyncio
import logging
import pathlib
import socket
import sys

import orjson
import pydantic
import requests
import sqlalchemy.schema

import configuration
import database.crud
import database.helpers
import database.tables
import enums
import models.requests
import tools

_service_settings = configuration.ServiceConfiguration()

# %% Configuration Variables
bind = f"0.0.0.0:{_service_settings.http_port}"
workers = 1
limit_request_line = 0
limit_request_fields = 0
limit_request_field_size = 0
max_requests = 0
timeout = 0
preload_app = False
worker_class = "uvicorn.workers.UvicornWorker"


# %% Events
def on_starting(server):
    logging.basicConfig(
        format="[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
        level=_service_settings.log_level,
        force=True,
    )
    # Try to read the configuration for connecting to the database
    try:
        _database_settings = configuration.DatabaseConfiguration()
    except pydantic.ValidationError as e:
        logging.critical("Unable to read the configuration for connecting to the database", exc_info=e)
        sys.exit(1)
    logging.info("Checking the connection to the database")
    _database_settings.dsn.port = 5432 if _database_settings.dsn.port is None else int(_database_settings.dsn.port)
    _database_available = asyncio.run(
        tools.is_host_available(host=_database_settings.dsn.host, port=_database_settings.dsn.port, timeout=10)
    )
    if not _database_available:
        logging.critical(
            "The database is not available. Since this service requires an access to the database the service will "
            "not start"
        )
        sys.exit(2)
    try:
        _gateway_information = configuration.KongGatewayInformation()
    except pydantic.ValidationError:
        logging.critical(
            "Unable to read the information about the Kong API Gateway. Please refer to the documentation for further "
            "instructions: KONG_INFORMATION_INVALID "
        )
        sys.exit(1)
    _gateway_reachable = asyncio.run(
        tools.is_host_available(_gateway_information.hostname, _gateway_information.admin_port)
    )
    if not _gateway_reachable:
        logging.critical("The api gateway is not available. Since the service needs to register itself on the ")
        sys.exit(2)
    if not database.engine.dialect.has_schema(database.engine, "authorization"):
        logging.info("Creating the 'authorization' schema in the specified database.")
        database.engine.execute(sqlalchemy.schema.CreateSchema("authorization"))
        database.tables.initialize()
        database.helpers.create_initial_data(pathlib.Path("./configuration/scopes.json").absolute())
    else:
        database.tables.initialize()
        required_scopes: list[dict] = orjson.loads(open("./configuration/scopes.json").read())
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
    # %% Register at the Kong gateway
    _gateway_information = configuration.KongGatewayInformation()
    logging.debug("Read the following information about the gateway:\n%s", _gateway_information.json(indent=2))
    # Try to get information about the upstream
    upstream_information_request = tools.query_kong(
        f"/upstreams/upstream_{_service_settings.name}", enums.HTTPMethod.GET
    )
    if upstream_information_request.status_code == 404:
        logging.warning("No upstream for this service found. Creating a new upstream in the API gateway...")
        new_upstream_information = {"name": f"upstream_{_service_settings.name}"}
        upstream_creation = tools.query_kong(
            f"/upstreams/",
            enums.HTTPMethod.POST,
            data=new_upstream_information,
        )
        if upstream_creation.status_code == 201:
            logging.info(
                "Created a new upstream for this service:\n%s",
                orjson.dumps(upstream_creation.json(), option=orjson.OPT_INDENT_2),
            )
        else:
            logging.debug(
                f"Received a {upstream_creation.status_code} from the gateway:\n%s",
                orjson.dumps(upstream_creation.json(), option=orjson.OPT_INDENT_2),
            )
    elif upstream_information_request.status_code == 200:
        logging.debug(
            "Found the following upstream information for this service:\n%s",
            orjson.dumps(upstream_information_request.json(), option=orjson.OPT_INDENT_2).decode("utf-8"),
        )

    service_information_request = tools.query_kong(f"/services/service_{_service_settings.name}", enums.HTTPMethod.GET)
    if service_information_request.status_code == 404:
        logging.warning("No service entry found for this service. Creating a new entry in the API gateway...")
        new_service_information = {
            "name": f"service_{_service_settings.name}",
            "host": f"upstream_{_service_settings.name}",
        }
        service_creation_request = tools.query_kong(f"/services/", enums.HTTPMethod.POST, new_service_information)
        if service_creation_request.status_code == 201:
            logging.info(
                "Created a new entry for this service:\n%s",
                orjson.dumps(service_creation_request.json(), option=orjson.OPT_INDENT_2).decode("utf-8"),
            )
    elif service_information_request.status_code == 200:
        logging.debug(
            "Found the following information for this service:\n%s",
            orjson.dumps(service_information_request.json(), option=orjson.OPT_INDENT_2).decode("utf-8"),
        )
    route_information_request = tools.query_kong(
        f"/services/service_" f"{_service_settings.name}/routes/{_gateway_information.service_path_slug}",
        method=enums.HTTPMethod.GET,
    )
    if route_information_request.status_code == 404:
        logging.warning("No route is configured for this service. Creating a new route definition for this service...")
        route_creation_request_data = {
            "paths[]": f"/{_gateway_information.service_path_slug}",
            "name": _gateway_information.service_path_slug,
        }
        route_creation_request = tools.query_kong(
            f"/services/service_{_service_settings.name}/routes/",
            method=enums.HTTPMethod.POST,
            data=route_creation_request_data,
        )
        if route_creation_request.status_code == 201:
            logging.info(
                "Created a new route for this service:\n%s",
                orjson.dumps(route_creation_request.json(), option=orjson.OPT_INDENT_2).decode("utf-8"),
            )
    # Determine the ip address of the service container
    ip_address = socket.gethostbyname(socket.gethostname())
    # Request information about the available targets
    upstream_target_information_request = tools.query_kong(
        f"/upstreams/upstream_{_service_settings.name}/targets", enums.HTTPMethod.GET
    )
    upstream_target_information = upstream_target_information_request.json()
    container_listed = any(
        [
            target["target"] == f"{ip_address}:{_service_settings.http_port}"
            for target in upstream_target_information["data"]
        ]
    )
    if not container_listed:
        upstream_target_creation_data = {"target": f"{ip_address}:{_service_settings.http_port}"}
        upstream_creation_request = tools.query_kong(
            f"/upstreams/upstream_{_service_settings.name}/targets",
            enums.HTTPMethod.POST,
            upstream_target_creation_data,
        )
        if upstream_creation_request.status_code == 201:
            logging.info(
                "Created a new upstream target for this service:\n%s",
                orjson.dumps(upstream_creation_request.json(), option=orjson.OPT_INDENT_2).decode("utf-8"),
            )
    consumer_information_request = tools.query_kong("/consumers", enums.HTTPMethod.GET)
    consumer_exists = any(
        [consumer["custom_id"] == "authorization-service" for consumer in consumer_information_request.json()["data"]]
    )
    _consumer_id = None
    if not consumer_exists:
        consumer_creation_request_data = {"custom_id": "authorization-service"}
        consumer_creation_request = tools.query_kong(
            "/consumers", data=consumer_creation_request_data, method=enums.HTTPMethod.POST
        )
        if consumer_creation_request.status_code == 201:
            logging.info(
                "Created new consumer for this service:\n%s",
                orjson.dumps(consumer_creation_request.json(), option=orjson.OPT_INDENT_2).decode("utf-8"),
            )
            _consumer_id = consumer_creation_request.json()["id"]
    else:
        _consumer_id = [
            consumer["id"]
            for consumer in consumer_information_request.json()["data"]
            if consumer["custom_id"] == "authorization-service"
        ][0]
    consumer_credential_information_request = tools.query_kong(
        f"/consumers/{_consumer_id}/oauth2", method=enums.HTTPMethod.GET
    )
    consumer_credentials_exists = any(
        [
            credential["consumer"]["id"] == _consumer_id
            for credential in consumer_credential_information_request.json()["data"]
        ]
    )
    if not consumer_credentials_exists:
        consumer_credential_creation_request_data = {
            "name": "Authorization Module",
            "redirect_uris": "http://localhost/authenticated",
        }
        consumer_credential_creation_request = tools.query_kong(
            f"/consumers/{_consumer_id}/oauth2",
            data=consumer_credential_creation_request_data,
            method=enums.HTTPMethod.POST,
        )
        if consumer_credential_creation_request.status_code == 201:
            logging.info(
                "Created new consumer credentials for this service:\n%s",
                orjson.dumps(consumer_credential_creation_request.json(), option=orjson.OPT_INDENT_2).decode("utf-8"),
            )
            credential_file = open("/.credential_id", "wt")
            credential_file.write(consumer_credential_creation_request.json()["id"])
    else:
        _credential_id = [
            credential["id"]
            for credential in consumer_information_request.json()["data"]
            if credential["consumer"]["id"] == _consumer_id
        ][0]
        credential_file = open("/.credential_id", "wt")
        credential_file.write(_credential_id)


def on_exit(server):
    _gateway_information = configuration.KongGatewayInformation()
    ip_address = socket.gethostbyname(socket.gethostname())
    upstream_deletion_request = requests.delete(
        f"http://{_gateway_information.hostname}:{_gateway_information.admin_port}/upstreams/upstream_"
        f"{_service_settings.name}/targets/{ip_address}:{_service_settings.http_port}",
    )
