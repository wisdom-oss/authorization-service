---
sidebar_label: user
title: db.crud.user
---

#### get\_user\_by\_id

```python
def get_user_by_id(db: Session, user_id: int) -> Optional[objects.User]
```

Get a ORM user object by the user id.

**Arguments**:

- `db`: Database Session which will be used to connect to the database
- `user_id`: ID of the user

**Returns**:

If there is no user with the given id None will be returned

#### get\_user\_by\_username

```python
def get_user_by_username(db: Session, username: str) -> Optional[objects.User]
```

Get a ORM user object by the username

**Arguments**:

- `db`: Database Session which will be used to connect to the database
- `username`: Username of the user

**Returns**:

The user or if there is no user by this username None

#### get\_users

```python
def get_users(db: Session) -> List[objects.User]
```

Get all users in the database

**Arguments**:

- `db`: Session which will be used to connect to the database

**Returns**:

List of users

#### add\_user

```python
def add_user(db: Session, new_user: data_models.NewUser) -> objects.User
```

Add a new user to the database

**Arguments**:

- `new_user`: The user which shall be inserted
- `db`: Database session

**Returns**:

Database ORM user

#### remove\_user

```python
def remove_user(db: Session, user_id: int)
```

Remove a user from the database. The user may only be removed if the user_id is known

**Arguments**:

- `db`: Database Session
- `user_id`: ID of the User which shall be removed

#### update\_user

```python
def update_user(db: Session, user_id: int, **new_values) -> objects.User
```

Update a user account

**Arguments**:

- `db`: Database session
- `user_id`: ID of the user which will be updated
- `new_values`: New values for the account. Available arguments are: first_name, last_name,
username, password, scopes, roles.
When passing scopes or roles all scopes or roles need to be passed to the function.

**Returns**:

The updated user

