"""This module will be used to execute the incoming messages"""
import logging
import typing

from pydantic import ValidationError

from models.amqp.outgoing import AMQPErrorResponse, BasicAMQPResponse
from models.amqp.incoming import *

__logger = logging.getLogger(__name__)

ResponseTypes = typing.TypeVar('ResponseTypes', AMQPErrorResponse, BasicAMQPResponse)


def execute(message: dict) -> ResponseTypes:
    """AMQP Message Executor

    This executor is responsible for selecting the correct forecasting procedures depending on
    the data present in the message. The message is expected as a dictionary.

    :param message: Message from the message broker
    :type message: bytes
    :return: Response which should be sent back to the message broker
    """
    try:
        # Convert the message into a incoming data model
        request = IncomingAMQPRequest.parse_obj(message)
    except ValidationError:
        return AMQPErrorResponse(
            error='INVALID_DATA_STRUCTURE',
            error_description='The data structure sent to the service did not match the '
                              'specification for this request type'
        )
    # Now check the type of payload and execute the payload specific code
    if isinstance(request.payload, AMQPValidateTokenRequest):
        # TODO: Implement token validation
        pass
    elif isinstance(request.payload, AMQPRevokeTokenRequest):
        # TODO: Implement token revocation
        pass
    else:
        return AMQPErrorResponse(
            error='NOT_IMPLEMENTED',
            error_description='The desired action is not fully implemented and therefore not '
                              'callable'
        )

