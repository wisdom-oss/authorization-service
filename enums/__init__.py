import enum


class HTTPMethod(enum.Enum):
    """A HTTP Request method"""

    GET = enum.auto()
    POST = enum.auto()
    PUT = enum.auto()
    PATCH = enum.auto()
    DELETE = enum.auto()
