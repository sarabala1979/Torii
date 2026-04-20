"""
Converts REST API endpoint definitions into MCP tools dynamically.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from torii.config import APIConfig, EndpointConfig, ParameterConfig


def _build_input_schema(parameters: list[ParameterConfig]) -> dict[str, Any]:
    """Build a JSON Schema object from a list of parameter configs."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for p in parameters:
        prop: dict[str, Any] = {
            "type": p.type,
            "description": p.description,
        }
        if p.default is not None:
            prop["default"] = p.default

        properties[p.name] = prop

        if p.required:
            required.append(p.name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema


class APITool:
    """
    An MCP tool backed by a REST API endpoint.
    Handles URL construction, auth headers, and HTTP execution.
    """

    def __init__(self, api: APIConfig, endpoint: EndpointConfig) -> None:
        self.api = api
        self.endpoint = endpoint
        self.name = endpoint.tool_name
        self.description = endpoint.description
        self.input_schema = _build_input_schema(endpoint.parameters)

    async def call(self, params: dict[str, Any]) -> str:
        """Execute the HTTP request and return the response as a string."""
        url = self.api.base_url + self.endpoint.path
        path_params: dict[str, str] = {}
        query_params: dict[str, Any] = {}
        body_params: dict[str, Any] = {}

        for p in self.endpoint.parameters:
            val = params.get(p.name, p.default)
            if val is None:
                continue
            match p.in_:
                case "path":
                    path_params[p.name] = str(val)
                case "query":
                    query_params[p.name] = val
                case "body":
                    body_params[p.name] = val

        # Substitute path parameters
        for key, val in path_params.items():
            url = url.replace(f"{{{key}}}", val)

        # Build headers: custom + auth
        headers = dict(self.api.headers)
        headers.update(self.api.auth.get_headers())
        if body_params:
            headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=self.endpoint.method,
                url=url,
                params=query_params or None,
                content=json.dumps(body_params).encode() if body_params else None,
                headers=headers,
            )

        if response.status_code >= 400:
            return f"Error {response.status_code}: {response.text}"

        # Try to return pretty-printed JSON, fall back to raw text
        try:
            return json.dumps(response.json(), indent=2)
        except Exception:
            return response.text


class APIConverter:
    """
    Converts an APIConfig into a list of APITool instances,
    one per endpoint defined in the config.
    """

    def convert(self, api: APIConfig) -> list[APITool]:
        """Return all tools for the given API config."""
        return [APITool(api, endpoint) for endpoint in api.endpoints]
