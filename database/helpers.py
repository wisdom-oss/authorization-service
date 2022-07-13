import logging
import pathlib

import orjson
import passlib.pwd

import models.requests
import database
import database.crud


def create_initial_data(scope_file: pathlib.Path):
    """
    Create the initial data in the database

    :param scope_file:
    :type scope_file:
    :return:
    :rtype:
    """
    # Read the scopes the service uses
    service_scopes: list[dict] = orjson.loads(scope_file.open().read())
    for service_scope in service_scopes:
        # Create an scope creation object
        scope = models.requests.ScopeCreationData(
            name=service_scope.get("name"),
            description=service_scope.get("description"),
            scope_string_value=service_scope.get("scopeStringValue"),
        )
        database.crud.store_new_scope(scope)
    # Now Create a new root user
    logging.warning("Creating new user and printing credentials to the stdout")
    # Generate a password using passlib
    password = passlib.pwd.genword(length=16)
    root_user = models.requests.AccountCreationInformation(
        first_name="Administrator",
        last_name="Administrator",
        username="root",
        scopes=[s.scope_string_value for s in database.crud.get_scopes()],
        password=password,
    )
    database.crud.store_new_user(root_user)
    logging.critical("==== ROOT ACCOUNT INFORMATION ====\nUsername: root\nPassword: %s", password)
