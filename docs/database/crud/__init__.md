---
sidebar_label: crud
title: database.crud
---

Package for the CREATE/READ/UPDATE/DELETE utilities


#### DBObject

Generic type for all database inserts


#### add\_to\_database

```python
def add_to_database(obj: DBObject, session: Session) -> DBObject
```

Insert a new object into the database

**Arguments**:

- `obj` (`X`): Object which shall be inserted
- `session`: Database session

**Returns**:

The inserted object

#### get\_all

```python
def get_all(table: typing.Type[DBObject], session: Session) -> list[DBObject]
```

Get all present entries of a table

**Arguments**:

- `table`: The table which shall be returned
- `session`: The session used to get the table entries

**Returns**:

A list of entries

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

#### add\_scope

```python
def add_scope(new_scope: models.shared.Scope, session: Session) -> tables.Scope
```

Add a new Scope to the system

**Arguments**:

- `new_scope`: The new scope for the environment
- `session`: The database session used to insert it

**Returns**:

The inserted scope

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

#### delete\_access\_token

```python
def delete_access_token(token_id: int, session: Session)
```

Delete an access token from the database

**Arguments**:

- `token_id`: 
- `session`: 

#### get\_refresh\_token

```python
def get_refresh_token(token_id: int, session: Session) -> typing.Optional[tables.RefreshToken]
```

Get an access token from the database by its internal id

**Arguments**:

- `token_id`: Internal Access Token ID
- `session`: Database session

**Returns**:

If the token exists the token, else None

#### get\_refresh\_token\_by\_token

```python
def get_refresh_token_by_token(token_value: str, session: Session) -> typing.Optional[tables.RefreshToken]
```

Get an access token from the database by its actual value

**Arguments**:

- `token_value`: The actual value of the access token
- `session`: Database session

**Returns**:

If the token exists the token, else None

#### delete\_refresh\_token

```python
def delete_refresh_token(token_id: int, session: Session)
```

Delete an access token from the database

**Arguments**:

- `token_id`: 
- `session`: 

#### get\_role

```python
def get_role(role_id: int, session: Session) -> tables.Role
```

Get a role by its id

**Arguments**:

- `role_id`: The internal role id
- `session`: The database session used to retrieve the role

**Returns**:

The role if it was found, else None

#### add\_role

```python
def add_role(new_role: models.http.incoming.Role, session: Session) -> tables.Role
```

Add a new role to the system

**Arguments**:

- `new_role`: The role which shall be inserted
- `session`: The session used to insert the role

**Returns**:

The inserted role

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

#### map\_scope\_to\_role

```python
def map_scope_to_role(role_id: int, scope_value: str, session: Session)
```

Map a scope to a role

**Arguments**:

- `session`: Database session
- `role_id`: Internal ID of the role
- `scope_value`: Name of the scope which shall be mapped to the role

#### clear\_mapping\_entries

```python
def clear_mapping_entries(table: typing.Type[tables.RoleToScope], main_key: int, db_session: Session)
```

Clear all mapping entries with the role id

**Arguments**:

- `table`: The mapping table which shall be cleared for the
- `main_key`: 
- `db_session`: 

#### get\_client\_credential\_by\_client\_id

```python
def get_client_credential_by_client_id(client_id: str, session: Session) -> tables.ClientCredential
```

Get a client credential from the database

**Arguments**:

- `client_id`: The client id which shall be queried for
- `session`: The database session used to access the database

