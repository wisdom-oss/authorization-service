---
sidebar_label: tools
title: tools
---

A collection of tools used multiple times throughout this service


#### resolve\_log\_level

```python
def resolve_log_level(level: str) -> int
```

Resolve the logging level from a string

This method will try to get the actual logging level from the logging package

If no valid logging level is supplied this method will return the info level

**Arguments**:

- `level`: The name of the level which should be resolved

**Returns**:

The logging level which may be used in the configuration of loggers

#### is\_host\_available

```python
async def is_host_available(host: str, port: int, timeout: int = 10) -> bool
```

Check if the specified host is reachable on the specified port

**Arguments**:

- `host`: The hostname or ip address which shall be checked
- `port`: The port which shall be checked
- `timeout`: Max. duration of the check

**Returns**:

A boolean indicating the status

#### create\_minimal\_database\_content

```python
def create_minimal_database_content(engine: Engine, session: Session)
```

Create the admin and me scopes and create a root user for initializing the authorization

service

**Arguments**:

- `engine`: The database engine via which the metadata is bound
- `session`: The database session which is used to insert the scopes and user

#### database\_contains\_active\_administrator

```python
def database_contains_active_administrator(session: Session)
```

Check if the database contains at least one active administrator

**Arguments**:

- `session`: 

