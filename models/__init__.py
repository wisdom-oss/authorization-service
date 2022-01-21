"""Module containing the data models for validating requests and responses as well as enabling
the settings"""
from pydantic import AnyHttpUrl, BaseSettings, Field, stricturl, AmqpDsn

# pylint: disable=too-few-public-methods


class ServiceSettings(BaseSettings):
    """
    Service Settings
    """
    database_dsn: stricturl(tld_required=False, allowed_schemes={"mariadb+pymysql",
                                                                 "mysql+pymysql"}) = Field(
        default=...,
        env='DATABASE_DSN',
        alias='DATABASE_DSN'
    )
    """URI pointing to a MariaDB or MySQL Database instance containing the authorization tables"""

    service_registry_url: AnyHttpUrl = Field(
        default=...,
        env='SERVICE_REGISTRY_URL',
        alias='SERVICE_REGISTRY_URL'
    )
    """URL pointing to a service registry installation (currently supported: Netflix Eureka)"""

    amqp_dsn: AmqpDsn = Field(
        default=...,
        env='AMQP_DSN',
        alias='AMQP_DSN'
    )
    """URI pointing the the message broker which shall be used to validate the messages"""

    amqp_exchange: str = Field(
        default="authorization-service",
        env='AMQP_EXCHANGE',
        alias='AMQP_EXCHANGE'
    )
    """Name of the Fanout Exchange this service will subscribe to"""
