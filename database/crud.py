import datetime
import hashlib
import http
import typing

import passlib.hash
import sqlalchemy.sql

import database
import database.tables
import exceptions
import models.common
import models.requests
import models.responses


# %% Operations for getting users
def get_user_account(identifier: typing.Union[str, int]):
    """
    Get the user account specified in the database

    :param identifier:
    :type identifier:
    :return:
    :rtype:
    """
    if type(identifier) is str:
        user_query = sqlalchemy.sql.select(
            [database.tables.accounts],
            database.tables.accounts.c.username == identifier,
        )
    elif type(identifier) is int:
        user_query = sqlalchemy.sql.select(
            [database.tables.accounts],
            database.tables.accounts.c.id == identifier,
        )
    else:
        raise TypeError("Expected identifier to by either string or int")
    user_query_result = database.engine.execute(user_query).first()
    if user_query_result is None:
        return user_query_result
    return models.common.UserAccount(
        id=user_query_result[0],
        first_name=user_query_result[1],
        last_name=user_query_result[2],
        username=user_query_result[3],
        password=user_query_result[4],
        active=user_query_result[5],
    )


def store_changed_user(user: models.common.UserAccount):
    update_user_query = (
        sqlalchemy.sql.update(database.tables.accounts)
        .where(database.tables.accounts.c.id == user.id)
        .values(
            firstName=user.first_name,
            lastName=user.last_name,
            username=user.username,
            password=user.password.get_secret_value(),
            active=user.active,
        )
    )
    database.engine.execute(update_user_query)


def delete_user(user):
    delete_user_query = sqlalchemy.sql.delete(database.tables.accounts).where(
        database.tables.accounts.c.id == user.id,
    )
    database.engine.execute(delete_user_query)


def get_user_accounts():
    user_account_query = sqlalchemy.sql.select(database.tables.accounts)
    user_account_query_results = database.engine.execute(user_account_query).all()
    user_accounts: list[models.responses.UserAccount] = []
    for user_account_query_result in user_account_query_results:
        account = models.common.UserAccount(
            id=user_account_query_result[0],
            first_name=user_account_query_result[1],
            last_name=user_account_query_result[2],
            username=user_account_query_result[3],
            password=user_account_query_result[4],
            active=user_account_query_result[5],
        )
        account_scopes = get_user_scopes(account)
        user_accounts.append(models.responses.UserAccount(**account.dict(), scopes=account_scopes))
    return user_accounts


def store_new_user(information: models.requests.AccountCreationInformation):
    user_insert_query = sqlalchemy.sql.insert(database.tables.accounts).values(
        firstName=information.first_name,
        lastName=information.last_name,
        username=information.username,
        password=passlib.hash.argon2.using(type="ID").hash(information.password.get_secret_value()),
        active=True,
    )
    database.engine.execute(user_insert_query)


# %% Operations for the scopes
def get_scope(identifier: typing.Union[str, int]):
    if type(identifier) is str:
        scope_query = sqlalchemy.sql.select(
            [database.tables.scopes],
            database.tables.scopes.c.value == identifier,
        )
    elif type(identifier) is int:
        scope_query = sqlalchemy.sql.select(
            [database.tables.scopes],
            database.tables.scopes.c.id == identifier,
        )
    else:
        raise TypeError("Expected identifier to by either string or int")
    scope_query_result = database.engine.execute(scope_query).first()
    if scope_query_result is None:
        return None
    return models.common.Scope(
        id=scope_query_result[0],
        name=scope_query_result[1],
        description=scope_query_result[2],
        scope_string_value=scope_query_result[3],
    )


def get_user_scopes(user: models.common.UserAccount) -> list[models.common.Scope]:
    scope_id_query = sqlalchemy.sql.select(
        [database.tables.account_scopes.c.scopeID],
        database.tables.account_scopes.c.accountID == user.id,
    )
    scope_id_query_result = database.engine.execute(scope_id_query).all()
    scope_ids = [result[0] for result in scope_id_query_result]
    return [get_scope(scope_id) for scope_id in scope_ids]


def set_user_scopes(user: models.common.UserAccount, scopes: list[models.common.Scope]):
    # Delete all scopes of the user
    delete_scope_assignment_query = sqlalchemy.sql.delete(database.tables.account_scopes).where(
        database.tables.account_scopes.c.accountID == user.id
    )
    database.engine.execute(delete_scope_assignment_query)
    # Now assign the scopes again
    for scope in scopes:
        insert_scope_assignment_query = sqlalchemy.sql.insert(
            database.tables.account_scopes
        ).values(scopeID=scope.id, accountID=user.id)
        database.engine.execute(insert_scope_assignment_query)


def get_access_token_scopes(token: models.common.TokenInformation) -> list[models.common.Scope]:
    scope_id_query = sqlalchemy.sql.select(
        [database.tables.access_token_scopes.c.scopeID],
        database.tables.access_token_scopes.c.tokenID == token.id,
    )
    scope_id_query_result = database.engine.execute(scope_id_query).all()
    scope_ids = [result[0] for result in scope_id_query_result]
    return [get_scope(scope_id) for scope_id in scope_ids]


def get_refresh_token_scopes(token: models.common.TokenInformation) -> list[models.common.Scope]:
    scope_id_query = sqlalchemy.sql.select(
        [database.tables.refresh_token_scopes.c.scopeID],
        database.tables.refresh_token_scopes.c.tokenID == token.id,
    )
    scope_id_query_result = database.engine.execute(scope_id_query).all()
    scope_ids = [result[0] for result in scope_id_query_result]
    return [get_scope(scope_id) for scope_id in scope_ids]


def store_changed_scope(scope: models.common.Scope):
    update_scope_query = (
        sqlalchemy.sql.update(database.tables.scopes)
        .where(database.tables.scopes.c.id == scope.id)
        .values(name=scope.name, description=scope.description)
    )
    database.engine.execute(update_scope_query)


def delete_scope(scope: models.common.Scope):
    update_scope_query = sqlalchemy.sql.delete(database.tables.scopes).where(
        database.tables.scopes.c.id == scope.id
    )
    database.engine.execute(update_scope_query)


def store_new_scope(scope_data: models.requests.ScopeCreationData):
    scope_insert_query = sqlalchemy.sql.insert(database.tables.scopes).values(
        name=scope_data.name,
        description=scope_data.description,
        value=scope_data.scope_string_value,
    )
    database.engine.execute(scope_insert_query)


def get_scopes():
    scope_query = sqlalchemy.sql.select(database.tables.scopes.c.id)
    scope_query_result = database.engine.execute(scope_query).all()
    return [get_scope(s[0]) for s in scope_query_result]


# %% Operations for manipulating access tokens
def insert_token_set(user: models.common.UserAccount, token_set: models.common.TokenSet) -> bool:
    current_time = datetime.datetime.now()
    insert_access_token_query = sqlalchemy.sql.insert(database.tables.access_token).values(
        value=hashlib.sha3_224(str(token_set.access_token).encode("utf-8")).hexdigest(),
        active=True,
        expires=current_time + datetime.timedelta(seconds=token_set.expires_in),
        created=current_time,
        accountID=user.id,
    )
    insert_refresh_token_query = sqlalchemy.sql.insert(database.tables.refresh_token).values(
        value=hashlib.sha3_224(token_set.refresh_token.encode("utf-8")).hexdigest(),
        active=True,
        expires=current_time + datetime.timedelta(days=3),
        accountID=user.id,
    )
    insert_access_token_result = database.engine.execute(insert_access_token_query)
    insert_refresh_token_result = database.engine.execute(insert_refresh_token_query)
    internal_access_token_id = insert_access_token_result.inserted_primary_key[0]
    internal_refresh_token_id = insert_refresh_token_result.inserted_primary_key[0]
    # Access the scope ids to populate the values for the token scopes
    scopes: list[models.common.Scope] = []
    for scope in token_set.scopes.split(" "):
        scopes.append(get_scope(scope))
    if None in scopes:
        raise exceptions.APIException(
            "INVALID_SCOPE_REQUESTED",
            "Invalid Scope Requested For Token",
            "You tried to request a scope which is not available to your account "
            "with your new access token",
            http.HTTPStatus.BAD_REQUEST,
        )
    for scope in scopes:
        insert_access_token_scope_query = sqlalchemy.sql.insert(
            database.tables.access_token_scopes
        ).values(tokenID=internal_access_token_id, scopeID=scope.id)
        insert_refresh_token_scope_query = sqlalchemy.sql.insert(
            database.tables.refresh_token_scopes
        ).values(tokenID=internal_refresh_token_id, scopeID=scope.id)
        database.engine.execute(insert_access_token_scope_query)
        database.engine.execute(insert_refresh_token_scope_query)
    return True


def get_access_token_data(identifier: typing.Union[str, int]):
    if type(identifier) is str:
        access_token_query = sqlalchemy.sql.select(
            [database.tables.access_token],
            database.tables.access_token.c.value
            == hashlib.sha3_224(identifier.encode("utf-8")).hexdigest(),
        )
    elif type(identifier) is int:
        access_token_query = sqlalchemy.sql.select(
            [database.tables.access_token],
            database.tables.access_token.c.id == identifier,
        )
    else:
        raise TypeError("Expected identifier to by either string or int")
    access_token_query_result = database.engine.execute(access_token_query).first()
    if access_token_query_result is None:
        return None
    return models.common.TokenInformation(
        id=access_token_query_result[0],
        value=access_token_query_result[1],
        active=access_token_query_result[2],
        expires=access_token_query_result[3],
        created=access_token_query_result[4],
        owner_id=access_token_query_result[5],
    )


def get_refresh_token_data(identifier: typing.Union[str, int]):
    if type(identifier) is str:
        access_token_query = sqlalchemy.sql.select(
            [database.tables.refresh_token],
            database.tables.refresh_token.c.value
            == hashlib.sha3_224(identifier.encode("utf-8")).hexdigest(),
        )
    elif type(identifier) is int:
        access_token_query = sqlalchemy.sql.select(
            [database.tables.refresh_token],
            database.tables.refresh_token.c.id == identifier,
        )
    else:
        raise TypeError("Expected identifier to by either string or int")
    access_token_query_result = database.engine.execute(access_token_query).first()
    if access_token_query_result is None:
        return None
    return models.common.TokenInformation(
        id=access_token_query_result[0],
        value=access_token_query_result[1],
        active=access_token_query_result[2],
        expires=access_token_query_result[3],
        owner_id=access_token_query_result[4],
    )


def delete_access_token(token: models.common.TokenInformation):
    delete_access_token_query = sqlalchemy.sql.delete(database.tables.access_token).where(
        database.tables.access_token.c.id == token.id,
    )
    database.engine.execute(delete_access_token_query)


def delete_refresh_token(token: models.common.TokenInformation):
    delete_refresh_token_query = sqlalchemy.sql.delete(database.tables.refresh_token).where(
        database.tables.refresh_token.c.id == token.id
    )
    database.engine.execute(delete_refresh_token_query)


def delete_all_access_tokens(user: models.common.UserAccount):
    delete_access_token_query = sqlalchemy.sql.delete(database.tables.access_token).where(
        database.tables.access_token.c.accountID == user.id,
    )
    database.engine.execute(delete_access_token_query)


def delete_all_refresh_tokens(user: models.common.UserAccount):
    delete_refresh_token_query = sqlalchemy.sql.delete(database.tables.refresh_token).where(
        database.tables.refresh_token.c.accountID == user.id,
    )
    database.engine.execute(delete_refresh_token_query)
