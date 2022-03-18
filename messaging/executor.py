"""This module will be used to execute the incoming messages"""
import logging
import typing

from pydantic import ValidationError

import database.tables
import security
from models.amqp.outgoing import AMQPErrorResponse, BasicAMQPResponse, AMQPScopeResponse
from models.amqp.incoming import *
from models.shared import TokenIntrospectionResult

__logger = logging.getLogger(__name__)

ResponseTypes = typing.TypeVar(
    'ResponseTypes',
    AMQPErrorResponse, TokenIntrospectionResult, AMQPScopeResponse, BasicAMQPResponse,
    AMQPCheckScopeRequest
)


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
        response = security.run_token_introspection(request.payload.token,
                                                    request.payload.scopes, amqp=True)
        
        return response
    elif isinstance(request.payload, AMQPCreateScopeRequest):
        _scope = database.tables.Scope(
            scope_name=request.payload.scope_name,
            scope_description=request.payload.scope_description,
            scope_value=request.payload.scope_value
        )
        scope = database.crud.add_to_database(_scope, next(database.session()))
        return AMQPScopeResponse.from_orm(scope)
    elif isinstance(request.payload, AMQPUpdateScopeRequest):
        # Create a db instance
        _session = next(database.session())
        # Get the scope from the database
        _scope = database.crud.get_scope(request.payload.scope_id, _session)
        # Edit the information that changed
        if request.payload.scope_name is not None and request.payload.scope_name.strip() != "":
            _scope.scope_name = request.payload.scope_name
        if request.payload.scope_description is not None and request.payload.scope_description.strip() != "":
            _scope.scope_description = request.payload.scope_description
        if request.payload.scope_value is not None and request.payload.scope_value.strip() != "":
            _scope.scope_value = request.payload.scope_value
        # Commit the changes and return the refreshed scope
        _session.commit()
        _session.refresh(_scope)
        return AMQPScopeResponse.parse_obj(_scope)
    elif isinstance(request.payload, AMQPDeleteScopeRequest):
        # Create a new db instance
        _session = next(database.session())
        # Get the scope from the database
        _scope = database.crud.get_scope(request.payload.scope_id, _session)
        # Call the session to delete this
        _session.delete(_scope)
        # Commit all changes
        _session.commit()
        # Return that this action was a success
        return BasicAMQPResponse()
    elif isinstance(request.payload, AMQPCheckScopeRequest):
        # Create a new db instance
        _session = next(database.session())
        # Check if a scope with this name exists
        _scope = database.crud.get_scope_by_value(request.payload.scope_value, _session)
        if _scope is None:
            return BasicAMQPResponse(status='false')
        else:
            return BasicAMQPResponse(status='true')
    else:
        return AMQPErrorResponse(
            error='NOT_IMPLEMENTED',
            error_description='The desired action is not fully implemented and therefore not '
                              'callable'
        )

