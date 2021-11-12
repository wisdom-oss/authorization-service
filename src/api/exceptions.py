"""Module for customized exceptions used with an error handler"""


class AuthorizationException(Exception):
    def __init__(self, error_code: str, needed_scope=""):
        self.error_code = error_code
        self.needed_scope = needed_scope
