---
sidebar_label: incoming
title: models.amqp.incoming
---

Package for describing the incoming amqp messages


## AMQPValidateTokenRequest Objects

```python
class AMQPValidateTokenRequest(BaseModel)
```

A data model for validating a token request


#### action

The action which shall be executed


#### token

The token which shall be validated


#### scopes

The scopes which shall be tested for the token


## AMQPCreateScopeRequest Objects

```python
class AMQPCreateScopeRequest(models.shared.Scope)
```

A data model describing the amqp payload which needs to be sent


#### action

The action which shall be executed


## AMQPUpdateScopeRequest Objects

```python
class AMQPUpdateScopeRequest(models.shared.ScopeUpdate)
```

#### action

The action which shall be executed


## AMQPDeleteScopeRequest Objects

```python
class AMQPDeleteScopeRequest(BaseModel)
```

#### action

The action which shall be executed


## IncomingAMQPRequest Objects

```python
class IncomingAMQPRequest(BaseModel)
```

A data model for incoming AMQP messages


