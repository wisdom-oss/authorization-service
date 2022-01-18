# Authorization and User Service
Maintainer: [Jan Eike Suchard](https://github.com/j-suchard)  
Version: 0.2  
Further documentation: [click here](../api/init)

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