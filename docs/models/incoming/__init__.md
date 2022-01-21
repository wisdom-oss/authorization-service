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


#### active

Status of the user (True == enabled)


#### scopes

Scopes of the new users


#### roles

Names of the roles which shall be assigned to the new user


## Config Objects

```python
class Config()
```

Configuration of this model


## ScopeUpdate Objects

```python
class ScopeUpdate(BaseModel)
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


## RoleUpdate Objects

```python
class RoleUpdate(BaseModel)
```

Data model for the Roles


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

Configuration for this data model


#### orm\_mode

Allow the reading of properties via a orm model


#### allow\_population\_by\_field\_name

Allow pydantic to use the field names to read the properties


#### allow\_population\_by\_alias

Allow pydantic to use the field aliases to read and assign properties


## Role Objects

```python
class Role(BaseModel)
```

Data model for the Role


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


