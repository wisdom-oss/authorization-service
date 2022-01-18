---
sidebar_label: models
title: models
---

Module containing the data models for validating requests and responses as well as enabling

the settings


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


