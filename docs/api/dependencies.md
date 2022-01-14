---
sidebar_label: dependencies
title: api.dependencies
---

Module for extra dependencies like own request bodies or database connections

#### get\_db\_session

```python
def get_db_session() -> DatabaseSession
```

Get a opened Database session which can be used to manipulate orm data

**Returns**:

`DatabaseSession`: Database Session

## CustomizedOAuth2PasswordRequestForm Objects

```python
class CustomizedOAuth2PasswordRequestForm()
```

This is a dependency class, use it like:

    @app.post(&quot;/login&quot;)
    def login(form_data: OAuth2PasswordRequestForm = Depends()):
        data = form_data.parse()
        print(data.username)
        print(data.password)
        for scope in data.scopes:
            print(scope)
        if data.client_id:
            print(data.client_id)
        if data.client_secret:
            print(data.client_secret)
        return data


It creates the following Form request parameters in your endpoint:

grant_type: the OAuth2 spec says it is required and MUST be the fixed string &quot;password&quot;.
    Nevertheless, this dependency class is permissive and allows not passing it. If you want
    to enforce it,
    use instead the OAuth2PasswordRequestFormStrict dependency.
username: username string. The OAuth2 spec requires the exact field name &quot;username&quot;.
password: password string. The OAuth2 spec requires the exact field name &quot;password&quot;.
scope: Optional string. Several scopes (each one a string) separated by spaces. E.g.
    &quot;items:read items:write users:read profile openid&quot;
client_id: optional string. OAuth2 recommends sending the client_id and client_secret (if any)
    using HTTP Basic auth, as: client_id:client_secret
client_secret: optional string. OAuth2 recommends sending the client_id and client_secret (if
any)
    using HTTP Basic auth, as: client_id:client_secret

