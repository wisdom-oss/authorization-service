"""Security related tools which will be used to validate tokens"""
from sqlalchemy.orm import Session
from passlib.hash import argon2


import database


def client_credentials_valid(
        client_id: str,
        client_secret: str,
        session: Session = next(database.session())
) -> bool:
    """Check if the supplied client credentials match and are valid

    :param session: The database session used to retrieve the database content
    :param client_id: The client id
    :param client_secret: The client secret
    :return: True if the client id/secret combination match those on record
    """
    # Try to get a database entry for the client_id
    _client_credentials = database.crud.get_client_credential_by_client_id(client_id, session)
    # Check if the query returned anything
    if _client_credentials is None:
        return False
    # Use the hashing method to validate if the client secret matches the one on the server and
    # return the result since a client credential allows the full access to the amqp interface
    return argon2.verify(client_secret, _client_credentials.client_secret)
