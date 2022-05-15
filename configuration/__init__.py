"""Module containing all configuration which are used in the application"""
import pydantic
from pydantic import BaseSettings, AmqpDsn, stricturl, Field


class ServiceConfiguration(BaseSettings):
    """Settings related to the general service execution"""

    name: str = Field(
        default="authorization-service",
        title="Service Name",
        description="The name of the service which is used for registering at the service "
        "registry and for identifying this service in amqp responses",
        env="CONFIG_SERVICE_NAME",
    )
    """
    Application Name
    
    The name of the service which is used for registering at the service registry and for
    identifying this service in amqp responses
    """

    http_port: int = Field(
        default=5000,
        title="HTTP Port",
        description="The HTTP port which will be bound by the internal HTTP server at the startup "
        "of this application",
        env="CONFIG_SERVICE_HTTP_PORT",
    )
    """
    HTTP Port
    
    The HTTP port which will be bound by the internal HTTP server at the startup of this service
    and is announced at the service registry
    """

    log_level: str = Field(
        default="INFO",
        title="Logging Level",
        description="The level of logging which the root logger will use",
        env="CONFIG_LOGGING_LEVEL",
    )
    """
    Logging Level
    
    The level of logging which will be used by the root logger
    """

    class Config:
        """Configuration of the service configuration"""

        env_file = ".env"
        """Allow loading the values for the service configuration from the specified file"""


class ServiceRegistryConfiguration(BaseSettings):
    """Settings related to the connection to the service registry"""

    host: str = Field(
        default=...,
        title="Service registry host",
        description="The hostname or ip address of the service registry on which this service "
        "shall register itself",
        env="CONFIG_SERVICE_REGISTRY_HOST",
    )
    """
    Service registry host (required)

    The hostname or ip address of the service registry on which this service shall register itself
    """

    port: int = Field(
        default=8761,
        title="Service registry port",
        description="The port on which the service registry listens on, defaults to 8761",
        env="CONFIG_SERVICE_REGISTRY_PORT",
    )
    """
    Service registry port

    The port on which the service registry listens on, defaults to 8761
    """

    class Config:
        """Configuration of the service registry configuration"""

        env_file = ".env"
        """The location of the environment file from which these values may be loaded"""


class DatabaseConfiguration(BaseSettings):
    """Settings related to the connections to the geo-data server"""

    dsn: pydantic.PostgresDsn = Field(
        default=...,
        title="PostgreSQL Database Service Name",
        description="A uri pointing to the mariadb containing the data for this service",
        env="CONFIG_DB_DSN",
    )
    """
    PostgreSQL Database Service Name

    An URI pointing to the installation of a PostgreSQL database which has the data required for
    this service
    """

    class Config:
        """Configuration of the AMQP related configuration"""

        env_file = ".env"
        """The file from which the configuration may be read"""
