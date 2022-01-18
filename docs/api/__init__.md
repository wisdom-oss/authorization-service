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

