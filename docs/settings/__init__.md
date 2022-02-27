---
sidebar_label: settings
title: settings
---

Module containing all settings which are used in the application


## ServiceSettings Objects

```python
class ServiceSettings(BaseSettings)
```

Settings related to the general service execution


#### name

Application Name

The name of the service which is used for registering at the service registry and for
identifying this service in amqp responses


#### http\_port

HTTP Port

The HTTP port which will be bound by the internal HTTP server at the startup of this service
and is announced at the service registry


#### log\_level

Logging Level

The level of logging which will be used by the root logger


## Config Objects

```python
class Config()
```

Configuration of the service settings


#### env\_file

Allow loading the values for the service settings from the specified file


## ServiceRegistrySettings Objects

```python
class ServiceRegistrySettings(BaseSettings)
```

Settings related to the connection to the service registry


#### host

Service registry host (required)

The hostname or ip address of the service registry on which this service shall register itself


#### port

Service registry port

The port on which the service registry listens on, defaults to 8761


## Config Objects

```python
class Config()
```

Configuration of the service registry settings


#### env\_file

The location of the environment file from which these values may be loaded


## AMQPSettings Objects

```python
class AMQPSettings(BaseSettings)
```

Settings related to AMQP-based communication


#### dsn

AMQP Address

The address pointing to a AMQP-enabled message broker which shall be used for internal
communication between the services


#### amqp\_exchange

AMQP Exchange

The exchange which is bound by the authorization service, defaults to `authorization-service`


## Config Objects

```python
class Config()
```

Configuration of the AMQP related settings


#### env\_file

The file from which the settings may be read


## DatabaseSettings Objects

```python
class DatabaseSettings(BaseSettings)
```

Settings related to the connections to the geo-data server


#### dsn

MariaDB Database Service Name

An URI pointing to the installation of a MariaDB database which has the data required for
this service


## Config Objects

```python
class Config()
```

Configuration of the AMQP related settings


#### env\_file

The file from which the settings may be read


