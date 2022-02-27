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


#### engine

```python
def engine() -> Engine
```

Get the raw database engine


#### initialise\_databases

```python
def initialise_databases()
```

Check if the database exists on the specified server and all tables are present


