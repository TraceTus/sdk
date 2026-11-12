"""The method of every operation, generated from the OpenAPI document.

Do not edit: ``scripts/generate.sh`` writes this file, and CI diffs it against
a fresh generation. The key is the module the generated package puts the
operation in, which is its ``operationId`` with the dot replaced.
"""

from __future__ import annotations

from collections.abc import Mapping

OPERATION_METHODS: Mapping[str, str] = {
    "connectors_add_device": "POST",  # /v1/connectors/{id}/devices
    "connectors_create": "POST",  # /v1/connectors
    "connectors_disable": "POST",  # /v1/connectors/{id}/disable
    "connectors_list": "GET",  # /v1/connectors
    "connectors_list_devices": "GET",  # /v1/connectors/{id}/devices
    "connectors_remove_device": "DELETE",  # /v1/connectors/{id}/devices/{deviceId}
    "health_get": "GET",  # /health
    "metrics_get": "GET",  # /v1/metrics
    "private_content_create": "POST",  # /v1/private-content
    "private_content_erase": "DELETE",  # /v1/private-content/{id}
    "private_content_get": "GET",  # /v1/private-content/{id}
    "private_content_list": "GET",  # /v1/private-content
    "records_create": "POST",  # /v1/records
    "records_create_batch": "POST",  # /v1/records/batch
    "records_get": "GET",  # /v1/records/{id}
    "verify_get": "GET",  # /v1/verify/{id}
}


def method_of(module_name: str) -> str:
    """The method of an operation module, or an empty string when unknown.

    Unknown counts as unsafe wherever this is read: it is the answer that keeps
    a caller from issuing twice.
    """
    return OPERATION_METHODS.get(module_name.rsplit(".", 1)[-1], "")
