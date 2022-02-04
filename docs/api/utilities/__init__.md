---
sidebar_label: utilities
title: api.utilities
---

This package holds some utilities which are used multiple times in the api implementation


#### ACCESS\_TOKEN\_TTL

TTL for a access token in seconds (1h)


#### REFRESH\_TOKEN\_TTL

TTL for a refresh token in seconds (7d)


#### generate\_token\_set

```python
def generate_token_set(user: database.tables.Account, db_session: Session, scopes: Optional[List[str]] = None) -> models.http.outgoing.TokenSet
```

Generate a new token set and insert it into the database

**Arguments**:

- `db_session`: The Database connection used to insert the token set
- `user`: The user for which the token set shall be generated
- `scopes`: The scopes this token is valid for (optional, defaults to any scope the user
has assigned)

**Returns**:

The generated Token Set

#### get\_scopes\_from\_user

```python
def get_scopes_from_user(_user: database.tables.Account) -> list[str]
```

Get a list of scope values from the account

**Arguments**:

- `_user` (`database.tables.Account`): The user account which shall be used

**Returns**:

A list of scope strings

#### field\_may\_be\_update\_source

```python
def field_may_be_update_source(new_value: Optional[str]) -> bool
```

Check if the field may be used for an update

The check is done by testing if the str is actually None and stripping the string does not
result in an empty string. This shall not be used for passwords, since those values may not
be stripped of any whitespaces

**Arguments**:

- `new_value`: The value the field shall have after the update

**Returns**:

True if the field may be used, False if it may not be used

