---
sidebar_label: outgoing
title: models.outgoing
---

Datamodels for outgoing data


## Scope Objects

```python
class Scope(BaseModel)
```

Data model for describing a scope which can be used in incoming/outgoing communication


#### scope\_id

Internally used id of the scope


#### scope\_name

Name of the scope


#### scope\_description

Textual description of the scope


#### scope\_value

OAuth2 scope string value identifying the scope


## Config Objects

```python
class Config()
```

Configuration of this model


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


#### active

Account Status (True == active)


#### scopes

All scopes assigned to this user


#### roles

Roles assigned to the user


## Config Objects

```python
class Config()
```

Configuration for this data model


#### orm\_mode

Allow the reading of properties via a orm model


#### allow\_population\_by\_field\_name

Allow pydantic to use the field names to read the properties


