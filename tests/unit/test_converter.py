"""Tests for the API → MCP tool converter."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from torii.api import APIConverter
from torii.config import APIConfig, AuthConfig, EndpointConfig, ParameterConfig


def make_api(endpoints=None) -> APIConfig:
    return APIConfig(
        name="test-api",
        base_url="https://api.example.com",
        auth=AuthConfig(type="bearer", token="test-token"),
        endpoints=endpoints or [],
    )


def make_endpoint(**kwargs) -> EndpointConfig:
    defaults = dict(
        path="/items/{id}",
        method="GET",
        tool_name="get_item",
        description="Get an item",
        parameters=[
            ParameterConfig(name="id", **{"in": "path"}, required=True, type="string"),
            ParameterConfig(name="fields", **{"in": "query"}, required=False, type="string"),
        ],
    )
    defaults.update(kwargs)
    return EndpointConfig(**defaults)


class TestAPIConverter:
    def test_converts_endpoints_to_tools(self):
        api = make_api([make_endpoint(), make_endpoint(tool_name="get_item_v2", path="/items2/{id}")])
        tools = APIConverter().convert(api)
        assert len(tools) == 2
        assert tools[0].name == "get_item"
        assert tools[1].name == "get_item_v2"

    def test_input_schema_has_properties(self):
        api = make_api([make_endpoint()])
        tool = APIConverter().convert(api)[0]
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "id" in schema["properties"]
        assert "fields" in schema["properties"]

    def test_required_params_in_schema(self):
        api = make_api([make_endpoint()])
        tool = APIConverter().convert(api)[0]
        assert "id" in tool.input_schema["required"]
        assert "fields" not in tool.input_schema.get("required", [])

    def test_empty_api_returns_no_tools(self):
        tools = APIConverter().convert(make_api([]))
        assert tools == []


class TestAPIToolCall:
    @pytest.mark.asyncio
    async def test_path_param_substituted(self, respx_mock):
        respx_mock.get("https://api.example.com/items/42").mock(
            return_value=httpx.Response(200, json={"id": 42})
        )
        api = make_api([make_endpoint()])
        tool = APIConverter().convert(api)[0]
        result = await tool.call({"id": "42"})
        assert "42" in result

    @pytest.mark.asyncio
    async def test_auth_header_sent(self, respx_mock):
        route = respx_mock.get("https://api.example.com/items/1").mock(
            return_value=httpx.Response(200, json={})
        )
        api = make_api([make_endpoint()])
        tool = APIConverter().convert(api)[0]
        await tool.call({"id": "1"})
        assert route.calls[0].request.headers["authorization"] == "Bearer test-token"

    @pytest.mark.asyncio
    async def test_error_response_returned(self, respx_mock):
        respx_mock.get("https://api.example.com/items/99").mock(
            return_value=httpx.Response(404, text="Not found")
        )
        api = make_api([make_endpoint()])
        tool = APIConverter().convert(api)[0]
        result = await tool.call({"id": "99"})
        assert "404" in result
