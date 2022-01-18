# Authorization and User Service
Maintainer: [Jan Eike Suchard](https://github.com/j-suchard)  
Version: 0.2  
Further documentation: [click here](./api/init)

## System Requirements
### for Development
- Python 3.9
- packages vom requirements.txt

This service offers the possibility to authorize users for frontend end backend
applications the release package will be known as 1.0 and will have the following
features:

- [X] Authorization of Users via HTTP
- [X] Issue Refresh Token and use them to receive a new access_token
- [X] Check tokens via HTTP
- [ ] Check tokens via AMQP
- [X] Run user related commands
- [X] Run Scope related commands via HTTP
- [X] Run Role related commands via HTTP

## Important Information
### 1. Access Tokens
The TTL (time-to-live) of an access token is 1 hour
### 2. Refresh Tokens
For every authorization request a refresh_token will be issued. The TTL of 
a refresh token is 7 days
### 3. Scopes
The scopes which were assigned to an access token will also be assigned to a 
refresh token. Therefore, requesting a new access token with a refresh token
will only grant the same scopes as specified in the original request. Extending
or changing scopes is not supported and will result in an authorization error 