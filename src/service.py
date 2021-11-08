"""Main module for starting the service"""
import logging

import pydantic.error_wrappers

from data_models.settings import ServiceSettings

LOGGER_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(lineno)s ' \
                '- %(message)s'
"""Format for the logger used throughout the service"""

if __name__ == '__main__':
    # Print a welcome message for signalizing, that the service is starting
    print('WISdoM Open Source Authorization Service is starting...')
    # Setup the logging for the service
    logging.basicConfig(
        format=LOGGER_FORMAT,
        force=True
    )


