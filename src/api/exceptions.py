"""Module for customized exceptions used with an error handler"""
from starlette import status


class AuthorizationException(Exception):
    def __init__(self, error_code: str, status_code: status, optional_data=""):
        self.error_code = error_code
        self.status_code = status_code
        self.optional_data = optional_data
