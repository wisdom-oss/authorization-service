"""Module containing all settings which are used in the application"""
from pydantic import BaseSettings, AmqpDsn, stricturl, Field


class ServiceSettings(BaseSettings):
    """Settings related to the general service execution"""
    
    name: str = Field(
        default='authorization-service',
        title='Service Name',
        description='The name of the service which is used for registering at the service '
                    'registry and for identifying this service in amqp responses',
        env='SERVICE_NAME'
    )
    """
    Application Name
    
    The name of the service which is used for registering at the service registry and for
    identifying this service in amqp responses
    """
    
    http_port: int = Field(
        default=5000,
        title='HTTP Port',
        description='The HTTP port which will be bound by the internal HTTP server at the startup '
                    'of this application',
        env='SERVICE_HTTP_PORT'
    )
    """
    HTTP Port
    
    The HTTP port which will be bound by the internal HTTP server at the startup of this service
    and is announced at the service registry
    """
    
    log_level: str = Field(
        default='INFO',
        title='Logging Level',
        description='The level of logging which the root logger will use',
        env='SERVICE_LOG_LEVEL'
    )
    """
    Logging Level
    
    The level of logging which will be used by the root logger
    """
    
    class Config:
        """Configuration of the service settings"""
        
        env_file = '.application.env'
        """Allow loading the values for the service settings from the specified file"""


class ServiceRegistrySettings(BaseSettings):
    """Settings related to the connection to the service registry"""
    
    host: str = Field(
        default=...,
        title='Service registry host',
        description='The hostname or ip address of the service registry on which this service '
                    'shall register itself',
        env='SERVICE_REGISTRY_HOST'
    )
    """
    Service registry host (required)

    The hostname or ip address of the service registry on which this service shall register itself
    """
    
    port: int = Field(
        default=8761,
        title='Service registry port',
        description='The port on which the service registry listens on, defaults to 8761',
        env='SERVICE_REGISTRY_PORT'
    )
    """
    Service registry port

    The port on which the service registry listens on, defaults to 8761
    """
    
    class Config:
        """Configuration of the service registry settings"""
        
        env_file = '.registry.env'
        """The location of the environment file from which these values may be loaded"""


class AMQPSettings(BaseSettings):
    """Settings related to AMQP-based communication"""
    
    dsn: AmqpDsn = Field(
        default=...,
        title='AMQP Address',
        description='The amqp address containing the login information into a message broker',
        env='AMQP_DSN'
    )
    """
    AMQP Address

    The address pointing to a AMQP-enabled message broker which shall be used for internal
    communication between the services
    """
    
    amqp_exchange: str = Field(
        default='authorization-service',
        title='Name of the exchange',
        description='Name of the exchange which is bound by the authorization service',
        env='AMQP_EXCHANGE'
    )
    """
    AMQP Exchange

    The exchange which is bound by the authorization service, defaults to `authorization-service`
    """

    class Config:
        """Configuration of the AMQP related settings"""
    
        env_file = '.amqp.env'
        """The file from which the settings may be read"""


class DatabaseSettings(BaseSettings):
    """Settings related to the connections to the geo-data server"""
    
    dsn: stricturl(
        tld_required=False,
        allowed_schemes={"mariadb+pymysql", "mysql+pymysql"}
    ) = Field(
        default=...,
        title='MariaDB Database Service Name',
        description='A uri pointing to the mariadb containing the data for this service',
        env='DATABASE_DSN'
    )
    """
    MariaDB Database Service Name

    An URI pointing to the installation of a MariaDB database which has the data required for
    this service
    """
    
    class Config:
        """Configuration of the AMQP related settings"""
        
        env_file = '.database.env'
        """The file from which the settings may be read"""
