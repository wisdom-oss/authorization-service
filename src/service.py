"""Main module for starting the service"""
import logging
import os
import sys

import pydantic.error_wrappers
import uvicorn

from data_models.settings import ServiceSettings

# Print a welcome message for signalizing, that the service is starting
print('WISdoM Open Source Authorization Service is starting...')

LOGGER_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(lineno)s ' \
                '- %(message)s'
"""Format for the logger used throughout the service"""

# Setup the logging for the service
logging.basicConfig(
        format=LOGGER_FORMAT,
        force=True,
        level=f'{os.getenv("LOG_LEVEL", default="DEBUG")}'
)

if __name__ == '__main__':

    # Create a logger for the main service bootstrapper
    logger = logging.getLogger('bootstrap')
    # Try reading the configuration for the service
    logger.debug('Trying to read the configuration from the environment variables.')
    try:
        config = ServiceSettings()
    except pydantic.error_wrappers.ValidationError as validation_error:
        logger.exception('The settings could not be read completely', exc_info=validation_error)
        sys.exit(1)
    logger.debug('The config now is %s', config)
    uvicorn.run(
        "api:auth_service",
        port=5000,
        host='0.0.0.0'
    )

