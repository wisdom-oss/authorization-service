---
sidebar_label: outgoing
title: models.amqp.outgoing
---

Package containing all outgoing response models


## BasicAMQPResponse Objects

```python
class BasicAMQPResponse(BaseModel)
```

A Basic Response Model for predefining some steps and properties of the models

All other outgoing models shall be based on this class


#### status

Status of the message handling


## AMQPErrorResponse Objects

```python
class AMQPErrorResponse(BasicAMQPResponse)
```

A Response Model used for errors which occurred during the message handling


#### status

Since this is a error response the status will be error


#### error

A short error name specifying the type of error


#### error\_description

A more accurate description of the error


## AMQPScopeResponse Objects

```python
class AMQPScopeResponse(shared.Scope,  BasicAMQPResponse)
```

Data model for describing a scope which can be used in incoming/outgoing communication


#### scope\_id

Internally used id of the scope


