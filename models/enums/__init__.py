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
