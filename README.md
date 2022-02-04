# Authorization Service
Maintainer: [Jan Eike Suchard](https://github.com/j-suchard)  
Version: 0.9

<hr/>

## Supported Features

- Access token issuing via HTTP
- User management via HTTP
- Role management via HTTP
- Scope management via HTTP

## Planned Features

- Creation of client credentials for internal modules
- Scope management via AMQP
- Authentication via client credentials via HTTP

<hr/>

## Usage Information

The general information about how to make requests may be found in the OpenAPI Specification of this
service

### Tokens

The following lifetimes are in reference to the creation time on the server. The creation time may 
be requested via running a token introspection.

#### Access Tokens

Access Tokens issued by this service are valid for `3600` seconds (1 hour).  
The access tokens are UUIDs (Type 4)

#### Refresh Tokens

Refresh Tokens issued by this service are valid for `604800` seconds (7 days)  
The refresh tokens are SHA512 hashed UUIDs (Type 4).  
When using a refresh token for getting a new access token the refresh token will be deleted and 
therefore invalidated

<hr/>

## Common Error Codes

### HTTP

#### DUPLICATE_ENTRY

During the creation of a new object a unique or primary key was violated. Please check the current
entries in the databases and try again. If the error persists, create an issue please.

#### invalid_grant

The credentials which were used during the authorization process are not valid. Please try again. 
If the error persists, contact your administrator

#### invalid_scope

The scopes which were requested during the authorization process are either not assigned to the user
tyring to authorize or are not in the system. Please check your tables, if needed and contact your 
administrator if the error persists

#### invalid_request

Some of your data was invalid and therefore the request could not be handled. 
Please check your request.

#### no_privileges

The currently authorized user is not allowed to access the resource due to 
missing scope assignments

### AMQP
#### INVALID_DATA_STRUCTURE

The data structure sent to the service did not match the specification for this 
request type

#### NOT_IMPLEMENTED

The action requested is currently not fully implemented and therefore not callable
