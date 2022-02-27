"""Package containing some custom Exceptions for handling certain events"""
from typing import Any, Optional

from starlette import status


class AuthorizationException(Exception):
    """
    An error occurred during authenticating a user which led to a non 2XX response
    """

    def __init__(
            self,
            short_error: str,
            error_description: Optional[str] = None,
            http_status_code: status = status.HTTP_400_BAD_REQUEST,
            optional_data: Optional[Any] = ""
    ):
        """Create a new Authorization Exception

        :param short_error: Short error description (e.g. USER_NOT_FOUND)
        :param error_description: Textual description of the error (may point to the documentation)
        :param http_status_code: HTTP Status code which shall be sent back by the error handler
        :param optional_data: Any optional data which shall be sent witch the error handler
        """
        super().__init__()
        self.short_error = short_error
        self.error_description = error_description
        self.http_status_code = http_status_code
        self.optional_data = optional_data


class ObjectNotFoundException(Exception):
    """
    An entry was not found in the database. This will trigger an HTTP Status 400 in the HTTP
    application part.
    """


class AMQPInvalidMessageFormat(Exception):
    """The AMQP message received by the authorization service did not match the required data
    structure"""
