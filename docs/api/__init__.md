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
    response_model=outgoing.TokenSet
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

