---
sidebar_label: database
title: database
---

Database module used for ORM descriptions of the used tables


#### session

```python
def session() -> DatabaseSession
```

Get an opened session for usage incoming the api dependencies


#### \_engine

```python
def _engine() -> Engine
```

Get the raw database engine


#### \_\_generate\_root\_user

```python
def __generate_root_user(__db_session: DatabaseSession = next(session()))
```

Generate a new root user with the user id of 0 and the admin and me scope


#### \_\_generate\_scopes

```python
def __generate_scopes(__db_session: DatabaseSession = next(session()))
```

Create the admin and me scope to enable a basic configuration


#### \_\_check\_required\_tables

```python
def __check_required_tables(__db_session: DatabaseSession = next(session()))
```

Check if at least one account exists in the database and the scopes &quot;me&quot; and &quot;admin&quot; are

present

**Arguments**:

- `__db_session`: Database session

#### initialise\_databases

```python
def initialise_databases()
```

Check if the database exists on the specified server and all tables are present


