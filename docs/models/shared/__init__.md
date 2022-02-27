---
sidebar_label: shared
title: models.shared
---

Package containing the data models which are shared throughout the application and access

methods


## TokenIntrospectionResult Objects

```python
class TokenIntrospectionResult(BaseModel)
```

Pydantic data model for a token introspection response


#### active

Status of the token (true if is active and not revoked)


#### scopes

Scopes this token was associated with


#### username

Username identifying the owner of the token


#### token\_type

Type of the token (either access_token or refresh_token)


#### exp

UNIX timestamp of expire time and date


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


