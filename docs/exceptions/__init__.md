---
sidebar_label: exceptions
title: exceptions
---

Package containing some custom Exceptions for handling certain events


## AuthorizationException Objects

```python
class AuthorizationException(Exception)
```

An error occurred during authenticating a user which led to a non 2XX response


#### \_\_init\_\_

```python
def __init__(short_error: str, error_description: Optional[str] = None, http_status_code: status = status.HTTP_400_BAD_REQUEST, optional_data: Optional[Any] = None)
```

Create a new Authorization Exception

**Arguments**:

- `short_error`: Short error description (e.g. USER_NOT_FOUND)
- `error_description`: Textual description of the error (may point to the documentation)
- `http_status_code`: HTTP Status code which shall be sent back by the error handler
- `optional_data`: Any optional data which shall be sent witch the error handler

## ObjectNotFoundException Objects

```python
class ObjectNotFoundException(Exception)
```

An entry was not found in the database. This will trigger an HTTP Status 400 in the HTTP

application part.


