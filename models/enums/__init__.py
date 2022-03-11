"""A package for organizing enumerations used throughout the project"""
from enum import Enum


class AMQPActions(str, Enum):
    """Actions which are available for AMQP messages"""

    VALIDATE_TOKEN = 'validate_token'
    """Request a token validation"""

    ADD_SCOPE = 'add_scope'
    """Add a scope to the system"""

    EDIT_SCOPE = 'edit_scope'
    """Edit a scope in the system"""

    DELETE_SCOPE = 'delete_scope'
    """Delete a scope present in the system"""
    
    CHECK_SCOPE = 'check_scope'
    """Check if a scope is present in the system"""
    

class TokenIntrospectionFailure(str, Enum):
    """Reasons for a failure of a token introspection"""
    
    INSUFFICIENT_SCOPE = 'insufficient_scope'
    TOKEN_ERROR = 'token_error'
