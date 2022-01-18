---
sidebar_label: crud
title: database.crud
---

Package for the CREATE/READ/UPDATE/DELETE utilities


#### X

Generic type for all database inserts


#### add\_to\_database

```python
def add_to_database(obj: X, session: Session) -> X
```

Insert a new object into the database

**Arguments**:

- `obj` (`X`): Object which shall be inserted
- `session`: Database session

**Returns**:

The inserted object

#### get\_users

```python
def get_users(session: Session) -> typing.List[tables.Account]
```

Get all users in the database

**Arguments**:

- `session`: Database session

#### get\_user

```python
def get_user(user_id: int, session: Session) -> typing.Optional[tables.Account]
```

Get an account by its internal id

**Arguments**:

- `user_id`: The internal user id
- `session`: Database connection

**Returns**:

The account data from the database

#### get\_user\_by\_username

```python
def get_user_by_username(username: str, session: Session) -> typing.Optional[tables.Account]
```

Get a users account by a username

**Arguments**:

- `username`: The username of the account
- `session`: Database session

**Returns**:

None if the user does not exist, else the orm account

#### add\_user

```python
def add_user(new_user: NewUserAccount, session: Session) -> tables.Account
```

Add a new user to the database

**Arguments**:

- `new_user`: New user which shall be created
- `session`: Database connection

**Returns**:

The created user

#### get\_scope

```python
def get_scope(scope_id: int, session: Session) -> typing.Optional[tables.Scope]
```

Get a scope from the database by its internal id

**Arguments**:

- `scope_id`: Internal ID of the scope
- `session`: Database session

**Returns**:

None if the scope does not exist, else the scope orm

#### get\_scope\_by\_value

```python
def get_scope_by_value(scope_value: str, session: Session) -> typing.Optional[tables.Scope]
```

Get a scope from the database by its scope value

**Arguments**:

- `scope_value`: Value of the scope for the scope string
- `session`: Database session

**Returns**:

None if the scope does not exist, else the orm representation of the scope

#### get\_access\_token

```python
def get_access_token(token_id: int, session: Session) -> typing.Optional[tables.AccessToken]
```

Get an access token from the database by its internal id

**Arguments**:

- `token_id`: Internal Access Token ID
- `session`: Database session

**Returns**:

If the token exists the token, else None

#### get\_access\_token\_by\_token

```python
def get_access_token_by_token(token_value: str, session: Session) -> typing.Optional[tables.AccessToken]
```

Get an access token from the database by its actual value

**Arguments**:

- `token_value`: The actual value of the access token
- `session`: Database session

**Returns**:

If the token exists the token, else None

#### map\_scope\_to\_account

```python
def map_scope_to_account(scope_value: str, account_id: int, session: Session) -> typing.Optional[tables.AccountToScope]
```

Map a scope to the account

**Arguments**:

- `scope_value`: Value of the scope to be assigned
- `account_id`: Internal id of the account which shall be using this scope,
- `session`: Database session

**Returns**:

The assignment if the scope exists and was assigned, else None

#### map\_role\_to\_account

```python
def map_role_to_account(role_name: str, account_id: int, session: Session)
```

Map a role to an account

**Arguments**:

- `role_name`: Name of the role
- `account_id`: Internal account id
- `session`: Database connection

**Returns**:

The association object if the insert was successful, else None

