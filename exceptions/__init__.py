"""Package containing some custom Exceptions for handling certain events"""
import http
from typing import Optional
from http import HTTPStatus


class APIException(Exception):
    """
    An error occurred during authenticating a user which led to a non 2XX response
    """

    def __init__(
        self,
        error_code: str,
        error_name: Optional[str] = None,
        error_description: Optional[str] = None,
        status_code: http.HTTPStatus = HTTPStatus.BAD_REQUEST,
    ):
        """Create a new Authorization Exception

        :param short_error: Short error description (e.g. USER_NOT_FOUND)
        :param error_description: Textual description of the error (may point to the documentation)
        :param status_code: HTTP Status code which shall be sent back by the error handler
        :param optional_data: Any optional data which shall be sent witch the error handler
        """
        super().__init__()
        self.error_code = error_code
        self.error_name = error_name
        self.error_description = error_description
        self.http_code = status_code


class ObjectNotFoundException(Exception):
    """
    An entry was not found in the database. This will trigger an HTTP Status 400 in the HTTP
    application part.
    """


class AMQPInvalidMessageFormat(Exception):
    """The AMQP message received by the authorization service did not match the required data
    structure"""
