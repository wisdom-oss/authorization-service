import asyncio
import time

import requests

import configuration
import enums
import models.common


async def is_host_available(host: str, port: int, timeout: int = 10) -> bool:
    """Check if the specified host is reachable on the specified port
    :param host: The hostname or ip address which shall be checked
    :param port: The port which shall be checked
    :param timeout: Max. duration of the check
    :return: A boolean indicating the status
    """
    _end_time = time.time() + timeout
    while time.time() < _end_time:
        try:
            # Try to open a connection to the specified host and port and wait a maximum time of five seconds
            _s_reader, _s_writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
            # Close the stream writer again
            _s_writer.close()
            # Wait until the writer is closed
            await _s_writer.wait_closed()
            return True
        except:
            # Since the connection could not be opened wait 5 seconds before trying again
            await asyncio.sleep(5)
    return False


def query_kong(path: str, method: enums.HTTPMethod, data: None | dict) -> requests.Response:
    _kong = configuration.KongGatewayInformation()
    match method:
        case enums.HTTPMethod.GET:
            return requests.get(f"http://{_kong.hostname}:{_kong.admin_port}{path}")
        case enums.HTTPMethod.POST:
            return requests.post(f"http://{_kong.hostname}:{_kong.admin_port}{path}", data=data)
        case enums.HTTPMethod.PUT:
            return requests.put(f"http://{_kong.hostname}:{_kong.admin_port}{path}", data=data)
        case enums.HTTPMethod.PATCH:
            return requests.patch(f"http://{_kong.hostname}:{_kong.admin_port}{path}", data=data)
        case enums.HTTPMethod.DELETE:
            return requests.delete(f"http://{_kong.hostname}:{_kong.admin_port}{path}", data=data)
        case _:
            raise Exception(
                "The function only supports the following HTTP request types: GET, POST, PUT, PATCH, DELETE"
            )


def store_token_in_gateway(token_set: models.common.TokenSet, username: str):
    credential_id = open("/.credential_id", "rt").read()
    request_data = {
        "credential.id": credential_id,
        "token_type": token_set.access_token_type,
        "access_token": token_set.access_token,
        "refresh_token": token_set.refresh_token,
        "expires_in": token_set.expires_in,
        "scope": token_set.scopes,
        "authenticated_userid": username,
    }
    response = query_kong("/oauth2_tokens", method=enums.HTTPMethod.POST, data=request_data)


def revoke_token_in_gateway(access_token: str):
    gateway_token_request = query_kong("/oauth2_tokens", method=enums.HTTPMethod.GET)
    token_id = [token["id"] for token in gateway_token_request.json() if token["access_token"] == access_token][0]
    gateway_token_revokation = query_kong(f"/oauth2_tokens/{token_id}", method=enums.HTTPMethod.DELETE)
