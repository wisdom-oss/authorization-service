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
async def handle_authorization_exception(_request: Request, e: AuthorizationException) -> UJSONResponse
```

Handle the Authorization exception

This handler will set the error information according to the data present in the exception.
Furthermore, the optional data will be passed in the `WWW-Authenticate` header.

**Arguments**:

- `_request`: The request in which the exception occurred in
- `e`: The Authorization Exception

**Returns**:

A UJSON response

