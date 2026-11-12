from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.add_connector_device_request import AddConnectorDeviceRequest
from ...models.connector_device_response import ConnectorDeviceResponse
from ...models.error_response import ErrorResponse
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: AddConnectorDeviceRequest,
    idempotency_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/connectors/{id}/devices".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ConnectorDeviceResponse | ErrorResponse | None:
    if response.status_code == 201:
        response_201 = ConnectorDeviceResponse.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 413:
        response_413 = ErrorResponse.from_dict(response.json())

        return response_413

    if response.status_code == 422:
        response_422 = ErrorResponse.from_dict(response.json())

        return response_422

    if response.status_code == 429:
        response_429 = ErrorResponse.from_dict(response.json())

        return response_429

    if response.status_code == 503:
        response_503 = ErrorResponse.from_dict(response.json())

        return response_503

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ConnectorDeviceResponse | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    body: AddConnectorDeviceRequest,
    idempotency_key: str,
) -> Response[ConnectorDeviceResponse | ErrorResponse]:
    """Register a device on a connector

    Args:
        id (str):  Example: con_0123456789abcdef0123456789abcdef.
        idempotency_key (str): A value unique to this call, 16 to 255 characters from A-Z, a-z,
            0-9 and the signs . _ : - . The first answer to a key is replayed for 24 hours, so a retry
            issues once; the same key with a different request is refused. Example:
            9f1c0f9e-6b4f-4f0a-9a0e-1c2d3e4f5a6b.
        body (AddConnectorDeviceRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectorDeviceResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: AuthenticatedClient,
    body: AddConnectorDeviceRequest,
    idempotency_key: str,
) -> ConnectorDeviceResponse | ErrorResponse | None:
    """Register a device on a connector

    Args:
        id (str):  Example: con_0123456789abcdef0123456789abcdef.
        idempotency_key (str): A value unique to this call, 16 to 255 characters from A-Z, a-z,
            0-9 and the signs . _ : - . The first answer to a key is replayed for 24 hours, so a retry
            issues once; the same key with a different request is refused. Example:
            9f1c0f9e-6b4f-4f0a-9a0e-1c2d3e4f5a6b.
        body (AddConnectorDeviceRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectorDeviceResponse | ErrorResponse
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    body: AddConnectorDeviceRequest,
    idempotency_key: str,
) -> Response[ConnectorDeviceResponse | ErrorResponse]:
    """Register a device on a connector

    Args:
        id (str):  Example: con_0123456789abcdef0123456789abcdef.
        idempotency_key (str): A value unique to this call, 16 to 255 characters from A-Z, a-z,
            0-9 and the signs . _ : - . The first answer to a key is replayed for 24 hours, so a retry
            issues once; the same key with a different request is refused. Example:
            9f1c0f9e-6b4f-4f0a-9a0e-1c2d3e4f5a6b.
        body (AddConnectorDeviceRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectorDeviceResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient,
    body: AddConnectorDeviceRequest,
    idempotency_key: str,
) -> ConnectorDeviceResponse | ErrorResponse | None:
    """Register a device on a connector

    Args:
        id (str):  Example: con_0123456789abcdef0123456789abcdef.
        idempotency_key (str): A value unique to this call, 16 to 255 characters from A-Z, a-z,
            0-9 and the signs . _ : - . The first answer to a key is replayed for 24 hours, so a retry
            issues once; the same key with a different request is refused. Example:
            9f1c0f9e-6b4f-4f0a-9a0e-1c2d3e4f5a6b.
        body (AddConnectorDeviceRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectorDeviceResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
