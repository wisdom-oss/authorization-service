"""Module for describing the services settings"""
from pydantic import BaseSettings, Field, stricturl


class ServiceSettings(BaseSettings):
    """Data model for the service settings"""
    # URL for connecting to the database backend storing the authorization data
    database_url: stricturl(tld_required=False, allowed_schemes={"mysql+pymysql"}) = Field(
        default=...,
        title='Database Connection String',
        description='The only supported scheme for connection strings is "mysql+mysqldb". '
                    'Therefore you currently may only connect your authorization service to an '
                    'MariaDB or MySQL database backend',
        alias='SQLALCHEMY_DATABASE_URL',
        env='SQLALCHEMY_DATABASE_URL'
    )

    eureka_url: str = Field(
        default=...,
        alias='EUREKA_HOST',
        env='EUREKA_HOST'
    )

