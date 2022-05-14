import typing

import passlib.hash

import database.crud
import models.common


def hash_password(password: str) -> str:
    """Hash the password that has been supplied and return the hashed value

    :param password: The clear-text password
    :type password: str
    :return: The hashed password
    :rtype: str
    """
    return passlib.hash.argon2.using(type="ID").hash(password)


def verify_password(password: str, hash: str) -> bool:
    """
    Check if the supplied password fits the supplied hash

    :param password: The clear-text password
    :type password: str
    :param hash: The hash of the password
    :type hash: str
    :return: True if the password and the hash matches
    :rtype: bool
    """
    return passlib.hash.argon2.verify(password, hash)


def generate_token_set(
    user: models.common.UserAccount, scopes: typing.Union[list[str], str]
) -> models.common.TokenSet:
    """
    Generate a new token set and insert it into the database

    :param user: The user for which the token set shall be generated
    :type user: models.common.UserAccount
    :param scopes: A list of the scopes the token shall get
    :type scopes: list[str]
    :return: The generated token set
    :rtype: models.common.TokenSet
    """
    # Check if any scopes have been supplied. If not pull all scopes from the database
    if type(scopes) is str and scopes.strip() == "":
        scopes = " ".join(
            [scope.scope_string_value for scope in database.crud.get_user_scopes(user)]
        )
    token_set = models.common.TokenSet(scopes=scopes)
    return token_set
