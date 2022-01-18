---
sidebar_label: dependencies
title: api.dependencies
---

Package containing some custom dependencies for the API application


#### get\_current\_user

```python
async def get_current_user(security_scopes: SecurityScopes, token: str = Depends(__oauth2_scheme), db_session: Session = Depends(session)) -> tables.Account
```

Resolve and check permissions for the current user via the given access token

**Arguments**:

- `security_scopes`: Scopes which are needed for accessing the endpoint
- `token`: Bearer Token
- `db_session`: Database session

**Returns**:

The currently active account

## OAuth2AuthorizationRequestForm Objects

```python
class OAuth2AuthorizationRequestForm()
```

This dependency will create the following Form request parameters in the endpoint using it

grant_type: The grant type used to obtain a new access and refresh token. Allowed values are
either &quot;password&quot; or &quot;refresh_token&quot;. Other grant types are not supported by this form

username:   The username used to obtain a new token set (Required if the grant type is
&quot;password&quot;, must not be sent if the grant_type is set to &quot;refresh_token&quot;)

password:   The password used to obtain a new token set (Required if the grant type is
&quot;password&quot;, must not be sent if the grant_type is set to &quot;refresh_token&quot;)

refresh_token: The refresh token used to obtain a new token set (Required if grant type is
&quot;refresh_token&quot;, must not be sent if the grant_type is set to &quot;password&quot;)


#### \_\_init\_\_

```python
def __init__(grant_type: str = Form(None, regex="(?:^password$|^refresh_token$)"), username: str = Form(None, min_length=1), password: SecretStr = Form(None, min_length=1), refresh_token: str = Form(
                None,
                regex="^[0-9a-fA-F]{8}\b-([0-9a-fA-F]{4}\b-){3}[0-9a-fA-F]{12}$"
            ), scope: str = Form(""))
```

Initialize the new OAuth2AuthorizationRequestForm

If you protect an endpoint with this form you may not pass the following form data:

Using &quot;password&quot; as grant_type -&gt; &quot;refresh_token&quot;
Using &quot;refresh_token&quot; as grant_type -&gt; &quot;username&quot;, &quot;password&quot;

The refresh tokens format is automatically validated using a regex.

**Arguments**:

- `grant_type` (`str`): Grant type (supported values: &quot;password&quot;, &quot;refresh_token&quot;)
- `username` (`str`): Username of the account
- `password` (`SecretStr`): Password of the account
- `refresh_token` (`str`): Refresh token issued by a different request
- `scope` (`str`): Scope string

