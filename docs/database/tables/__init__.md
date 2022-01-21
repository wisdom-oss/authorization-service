---
sidebar_label: tables
title: database.tables
---

SQLAlchemy-compatible object relational mappings for the used tables


#### FK\_OPTIONS

Default options for the foreign key relations


## Role Objects

```python
class Role(TableDeclarationBase)
```

ORM mapping for the table containing the used roles


#### \_\_tablename\_\_

Name of the table incoming the database


#### role\_id

Internal ID of the role


#### role\_name

Name of the role (max. length 255, must be unique)


#### role\_description

Textual description of the role


#### scopes

Scopes assigned to this role


## Scope Objects

```python
class Scope(TableDeclarationBase)
```

ORM for the table containing the available scopes


#### \_\_tablename\_\_

Name of the table incoming the database


#### scope\_id

Internal id of the scope


#### scope\_name

Name of the scope


#### scope\_description

Textual description of the scope


#### scope\_value

String used to identify the scope incoming OAuth2 scope strings


## AccessToken Objects

```python
class AccessToken(TableDeclarationBase)
```

ORM for the Authorization Tokens


#### \_\_tablename\_\_

Name of the table incoming the database


#### token\_id

Internal id of the token


#### token

Actual token used incoming the Authorization header


#### active

Status of the token


#### expires

Expiration date and time as UNIX Timestamp


#### created

Creation date and time as UNIX Timestamp


#### user

User which is assigned to this token


#### scopes

Scopes associated with that token


## RefreshToken Objects

```python
class RefreshToken(TableDeclarationBase)
```

ORM for the refresh tokens


#### \_\_tablename\_\_

Name of the table incoming the database


#### refresh\_token\_id

Internal id of the refresh token


#### refresh\_token

Actual refresh token


#### expires

Expiration time and date as UNIX timestamp


#### user

The user of the refresh token


## Account Objects

```python
class Account(TableDeclarationBase)
```

ORM for the account table


#### \_\_tablename\_\_

Name of the table incoming the database


#### account\_id

Internal numeric account id


#### first\_name

First name(s) of the user associated to the account


#### last\_name

Last name(s) of the user associated to the account


#### username

Username for the account


#### password

Hashed password for the account


#### is\_active

Status of the account


#### scopes

Scopes assigned to the account


#### roles

Roles assigned to the account


## RoleToScope Objects

```python
class RoleToScope(TableDeclarationBase)
```

ORM for linking roles to the scopes they inherit


#### \_\_tablename\_\_

Name of the association table


#### mapping\_id

Internal ID of the mapping (needed for sqlalchemy)


#### role\_id

ID of the role


#### scope\_id

ID of the scope ofr this role


## TokenToScopes Objects

```python
class TokenToScopes(TableDeclarationBase)
```

ORM for linking the issued tokens to the scopes they may use


#### \_\_tablename\_\_

Name of the association table


#### mapping\_id

Internal ID of the mapping (needed for sqlalchemy)


#### token\_id

ID of the Access Token


#### scope\_id

ID of the scope for this token


## RefreshTokenToScopes Objects

```python
class RefreshTokenToScopes(TableDeclarationBase)
```

ORM for linking the issued tokens to the scopes they may use


#### \_\_tablename\_\_

Name of the association table


#### mapping\_id

Internal ID of the mapping (needed for sqlalchemy)


#### token\_id

ID of the Access Token


#### scope\_id

ID of the scope for this token


## TokenToRefreshToken Objects

```python
class TokenToRefreshToken(TableDeclarationBase)
```

ORM for linking a token to a refresh token


#### mapping\_id

Internal ID of the mapping (needed for sqlalchemy)


#### refresh\_token\_id

Internal ID of the refresh token


#### access\_token\_id

Internal ID of the access token


## AccountToScope Objects

```python
class AccountToScope(TableDeclarationBase)
```

ORM for linking accounts to the scopes


#### \_\_tablename\_\_

Name of the association table


#### mapping\_id

Internal ID of the mapping (needed for sqlalchemy)


#### account\_id

Internal id of the account


#### scope\_id

ID of the scope assigned to the account


## AccountToRoles Objects

```python
class AccountToRoles(TableDeclarationBase)
```

ORM for linking accounts to the roles


#### \_\_tablename\_\_

Name of the association table


#### mapping\_id

Internal ID of the mapping (needed for sqlalchemy)


#### account\_id

Internal ID of the account


#### role\_id

ID of the role assigned to the account


## AccountToToken Objects

```python
class AccountToToken(TableDeclarationBase)
```

ORM for linking accounts to their tokens


#### \_\_tablename\_\_

Name of the association table


#### mapping\_id

Internal ID of the mapping (needed for sqlalchemy)


#### account\_id

Internal ID of the account


#### token\_id

ID of the token issued via this account


## AccountToRefreshTokens Objects

```python
class AccountToRefreshTokens(TableDeclarationBase)
```

ORM for linking an account to their refresh tokens


#### \_\_tablename\_\_

Name of the association table


#### mapping\_id

Internal ID of the mapping (needed for sqlalchemy)


#### account\_id

Internal ID of the account


#### refresh\_token\_id

ID of the refresh token for the account


