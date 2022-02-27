---
sidebar_label: security
title: security
---

Security related tools which will be used to validate tokens


#### client\_credentials\_valid

```python
def client_credentials_valid(client_id: str, client_secret: str, session: Session = next(database.session())) -> bool
```

Check if the supplied client credentials match and are valid

**Arguments**:

- `session`: The database session used to retrieve the database content
- `client_id`: The client id
- `client_secret`: The client secret

**Returns**:

True if the client id/secret combination match those on record

#### run\_token\_introspection

```python
def run_token_introspection(token: str, scope: str, session: Session = next(database.session())) -> TokenIntrospectionResult
```

Execute a token introspection and return the result of the introspection

**Arguments**:

- `token`: The token which shall be introspected
- `scope`: The scopes against which the token shall be tested
- `session`: The database session which is used to access the data

**Returns**:

`TokenIntrospectionResult`: A TokenIntrospectionResult

