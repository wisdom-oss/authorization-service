---
sidebar_label: amqp
title: models.amqp
---

Package describing a basic data model to allow


## AMQPBaseModel Objects

```python
class AMQPBaseModel(BaseModel)
```

A preconfigured class for all AMQP models which also contains some necessary information

for later operations


#### action

The action which shall be executed


#### correlation\_id

AMQP Correlation ID sent with the original request


## Config Objects

```python
class Config()
```

Model configuration which is inherited by other models


#### use\_enum\_values

If a enumeration is used as datatype set the value to the field and not the enum


#### allow\_population\_by\_field\_name

Allow pydantic to assign a field by its name as well as the alias


#### smart\_union

Let pydantic check all types noted in a union before setting the type


