---
sidebar_label: models
title: models
---

Module containing the data models for validating requests and responses as well as enabling

the settings


## BaseModel Objects

```python
class BaseModel(PydanticBaseModel)
```

A basic data model containing a configuration which will be inherited into other models


## Config Objects

```python
class Config()
```

The basic configuration for every model


#### orm\_mode

Allow the model to read information of ORMs


#### allow\_population\_by\_field\_name

Allow pydantic to populate fields by their name and not alias during parsing of

objects, raw input or ORMs


## ServiceSettings Objects

```python
class ServiceSettings(BaseSettings)
```

Service Settings


#### database\_dsn

URI pointing to a MariaDB or MySQL Database instance containing the authorization tables


#### service\_registry\_url

URL pointing to a service registry installation (currently supported: Netflix Eureka)


#### amqp\_dsn

URI pointing the the message broker which shall be used to validate the messages


#### amqp\_exchange

Name of the Fanout Exchange this service will subscribe to


