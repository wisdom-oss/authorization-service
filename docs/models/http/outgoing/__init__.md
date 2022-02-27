---
sidebar_label: outgoing
title: models.http.outgoing
---

Datamodels for outgoing data


## Scope Objects

```python
class Scope(models.shared.Scope)
```

Data model for describing a scope which can be used in incoming/outgoing communication


#### scope\_id

Internally used id of the scope


## Config Objects

```python
class Config()
```

Configuration for this pydantic model


#### orm\_mode

Allow the reading of properties via a orm model


#### allow\_population\_by\_field\_name

Allow pydantic to use the field names to read the properties


#### allow\_population\_by\_alias

Allow pydantic to use the aliases to read properties


## Role Objects

```python
class Role(BaseModel)
```

Data model for the Roles


#### role\_id

Internal id used to identify the role


#### role\_name

Name of the role


#### role\_description

Textual description of the role


#### role\_scopes

Scopes assigned to the role


## Config Objects

```python
class Config()
```

Configuration for this pydantic model


#### orm\_mode

Allow the reading of properties via a orm model


#### allow\_population\_by\_field\_name

Allow pydantic to use the field names to read the properties


#### allow\_population\_by\_alias

Allow pydantic to use the aliases to read properties


## UserAccount Objects

```python
class UserAccount(BaseModel)
```

Datamodel describing the outgoing data about a user account


#### account\_id

Internal Account ID


#### first\_name

First name(s) of the person associated to this account


#### last\_name

Last name(s) of the person associated to this account


#### username

Username for this account


#### is\_active

Account Status (True == active)


#### scopes

All scopes assigned to this user


#### roles

Roles assigned to the user


## Config Objects

```python
class Config()
```

Configuration for this pydantic model


#### orm\_mode

Allow the reading of properties via a orm model


#### allow\_population\_by\_field\_name

Allow pydantic to use the field names to read the properties


#### allow\_population\_by\_alias

Allow pydantic to use the aliases to read properties


## TokenSet Objects

```python
class TokenSet(BaseModel)
```

Data model for a token set after a successful authorization attempt


#### access\_token

OAuth2 Bearer Token


#### token\_type

Type of the OAuth2 Token


#### expires\_in

TTL (time-to-live) of the token after it has been issued (Standard TTL: 3600)


#### refresh\_token

Refresh token which may be used to get a new access token


#### scope

Scope string for this token (optional if the token has the same scopes as requested)


## Config Objects

```python
class Config()
```

Configuration for this pydantic model


#### orm\_mode

Allow the reading of properties via a orm model


#### allow\_population\_by\_field\_name

Allow pydantic to use the field names to read the properties


#### allow\_population\_by\_alias

Allow pydantic to use the aliases to read properties


## ClientCredential Objects

```python
class ClientCredential(BaseModel)
```

Data model for a newly created client credential

Client credentials are only usable via AMQP and have no expiration


## Config Objects

```python
class Config()
```

Configuration for this pydantic model


#### orm\_mode

Allow the reading of properties via a orm model


#### allow\_population\_by\_field\_name

Allow pydantic to use the field names to read the properties


#### allow\_population\_by\_alias

Allow pydantic to use the aliases to read properties


## NewClientCredential Objects

```python
class NewClientCredential(BaseModel)
```

Data model for a newly created client credential

Client credentials are only usable via AMQP and have no expiration


## Config Objects

```python
class Config()
```

Configuration for this pydantic model


#### orm\_mode

Allow the reading of properties via a orm model


#### allow\_population\_by\_field\_name

Allow pydantic to use the field names to read the properties


#### allow\_population\_by\_alias

Allow pydantic to use the aliases to read properties


