"""Module for organizing some database related functions needed later during the initialization
and the read/write processes"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from data_models.settings import ServiceSettings

# Read the configuration again
# Since the configuration already has been read successfully a new check should not be needed
configuration = ServiceSettings()

# Create a new database engine from the database url
engine = create_engine(
    configuration.database_url, pool_recycle=60
)

# Create a database session which will be needed later on
DatabaseSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a declarative base for the table definitions
TableBase = declarative_base()
