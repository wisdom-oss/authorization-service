---
sidebar_label: api
title: api
---

Module containing the routes and actions run when requesting a specific route


#### auth\_service\_rest

Main API application for this service


#### api\_startup

```python
@auth_service_rest.on_event('startup')
def api_startup()
```

Event handler for the startup.

The code will be executed before any HTTP incoming will be accepted


#### api\_shutdown

```python
@auth_service_rest.on_event('shutdown')
def api_shutdown()
```

Event handler for the shutdown process of the application


#### handle\_authorization\_exception

```python
@auth_service_rest.exception_handler(AuthorizationException)
async def handle_authorization_exception(_request: Request, exc: AuthorizationException) -> UJSONResponse
```

Handle the Authorization exception

This handler will set the error information according to the data present in the exception.
Furthermore, the optional data will be passed in the `WWW-Authenticate` header.

**Arguments**:

- `_request` (`Request`): The request in which the exception occurred in
- `exc` (`AuthorizationException`): The Authorization Exception

**Returns**:

`UJSONResponse`: A JSON response explaining the reason behind the error

#### oauth\_login

```python
@auth_service_rest.post(
    path='/oauth/token',
    response_model=outgoing.TokenSet,
    response_model_exclude_none=True
)
async def oauth_login(form: dependencies.OAuth2AuthorizationRequestForm = Depends(), db_session: Session = Depends(database.session)) -> outgoing.TokenSet
```

Try to receive a token set with either username/password credentials or a refresh token

**Arguments**:

- `form` (`OAuth2AuthorizationRequestForm`): Authorization Request Data
- `db_session` (`Session`): Database session needed to validate the request data

**Raises**:

- `exceptions.AuthorizationException`: The request failed due to an error
during the users authorization

**Returns**:

`outgoing.TokenSet`: Token Set

#### oauth\_token\_introspection

```python
@auth_service_rest.post(
    path='/oauth/check_token',
    response_model=outgoing.TokenIntrospection,
    response_model_exclude_none=True
)
async def oauth_token_introspection(_active_user: tables.Account = Security(dependencies.get_current_user), db_session: Session = Depends(database.session), token: str = Form(...), scope: Optional[str] = Form(None)) -> outgoing.TokenIntrospection
```

Run an introspection of a token to check its validity

The check may be run as check for the general validity. It also may be run against one or
more scopes which will return the validity for the scopes sent in the request

**Arguments**:

- `_active_user`: The user making the request (not used here but still needed)
- `db_session`: The database session
- `token`: The token on which an introspection shall be executed
- `scope`: The scopes against which the token shall be tested explicitly

**Returns**:

The introspection response

#### oauth\_revoke\_token

```python
@auth_service_rest.post(
    path='/oauth/revoke',
    status_code=200
)
async def oauth_revoke_token(_active_user: tables.Account = Security(dependencies.get_current_user, scopes=["me"]), db_session: Session = Depends(database.session), token: str = Form(...))
```

Revoke any type of token

The revocation request will always be answered by an HTTP Code 200 code. Even if the token
was not found.

**Arguments**:

- `_active_user`: The user making the request
- `db_session`: The database session
- `token`: The token which shall be revoked

#### users\_get\_own\_account\_info

```python
@auth_service_rest.get(
    path='/users/me',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True
)
async def users_get_own_account_info(_active_user: tables.Account = Security(dependencies.get_current_user, scopes=["me"])) -> outgoing.UserAccount
```

Get information about the authorized user making this request

**Arguments**:

- `_active_user`: The user making the request

**Returns**:

The account information

#### user\_update\_own\_account\_password

```python
@auth_service_rest.patch(
    path='/users/me',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True
)
async def user_update_own_account_password(_active_user: tables.Account = Security(dependencies.get_current_user, scopes=["me"]), db_session: Session = Depends(database.session), old_password: SecretStr = Body(..., embed=True), new_password: SecretStr = Body(..., embed=True)) -> outgoing.UserAccount
```

Allow the current user to update the password assigned to the account

**Arguments**:

- `_active_user`: The user whose password shall be updated
- `db_session`: Database connection used for changing the password
- `old_password`: The old password needed for confirming the password change
- `new_password`: The new password which shall be set

**Returns**:

The account after the password change

#### users\_get\_user\_information

```python
@auth_service_rest.get(
    path='/users/{user_id}',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def users_get_user_information(user_id: int, _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]), db_session: Session = Depends(database.session)) -> outgoing.UserAccount
```

Get information about a specific user account by its internal id

**Arguments**:

- `user_id`: The internal account id
- `_active_user`: The user making the request
- `db_session`: The database session for retrieving the account data

**Returns**:

The account data

#### users\_update\_user\_information

```python
@auth_service_rest.patch(
    path='/users/{user_id}',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def users_update_user_information(user_id: int, _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]), db_session: Session = Depends(database.session), update_info: incoming.UserUpdate = Body(...)) -> Union[outgoing.UserAccount, Response]
```

Update a users account information

Since this is an admin endpoint no additional verification is necessary to change passwords.
Use with caution

**Arguments**:

- `user_id`: The id of the user which shall be updated
- `_active_user`: The user making the request
- `db_session`: The database session used to manipulate the user
- `update_info`: The new account information

**Returns**:

The updated account information

#### users\_delete

```python
@auth_service_rest.delete(
    path='/users/{user_id}'
)
async def users_delete(user_id: int, _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]), db_session: Session = Depends(database.session))
```

Delete a user by its internal id

**Arguments**:

- `user_id`: Account ID of the account which shall be deleted
- `_active_user`: Currently active user
- `db_session`: Database session

**Returns**:

A `200 OK` response if the user was deleted. If the user was not found 404

#### users\_get\_all

```python
@auth_service_rest.get(
    path='/users',
    response_model=list[outgoing.UserAccount],
    response_model_exclude_none=True
)
async def users_get_all(_active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]), db_session: Session = Depends(database.session))
```

Get a list of all user accounts

**Arguments**:

- `_active_user`: 
- `db_session`: 

#### users\_add

```python
@auth_service_rest.put(
    path='/users',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED
)
async def users_add(_active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]), db_session: Session = Depends(database.session), new_user: incoming.NewUserAccount = Body(...))
```

Add a user to the database

**Arguments**:

- `_active_user`: The user making the request
- `db_session`: The session used to insert the new user
- `new_user`: The new user to be inserted

