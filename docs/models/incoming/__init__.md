---
sidebar_label: incoming
title: models.incoming
---

Module containing the pydantic data models for incoming requests


## NewUserAccount Objects

```python
class NewUserAccount(BaseModel)
```

New user account. This model only needs some basic information


#### first\_name

First name(s) of the new user


#### last\_name

Last name(s) of the new user


#### username

Username of the user


#### password

Password of the new user


#### scopes

Scopes of the new users


#### roles

Names of the roles which shall be assigned to the new user


## Config Objects

```python
class Config()
```

Configuration of this model


## Scope Objects

```python
class Scope(BaseModel)
```

OAuth2 Scope


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


## UserUpdate Objects

```python
class UserUpdate(BaseModel)
```

A dataclass making all user account information of the new user optional


#### first\_name

First name(s) of the new user


#### last\_name

Last name(s) of the new user


#### username

Username of the user


#### password

Password of the new user


#### scopes

Scopes of the new users


#### roles

Names of the roles which shall be assigned to the new user


## Config Objects

```python
class Config()
```

Configuration of this model


