"""
Torii MCP Gateway — exposes all registered tools (from APIs + upstream MCP servers)
as a single unified MCP server using the MCP Python SDK.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from torii.api import APIConverter, APITool
from torii.config import ToriiConfig
from torii.mcp.aggregator import MCPAggregator
from torii.workflow import WorkflowEngine

logger = logging.getLogger(__name__)


class ToriiGateway:
    """
    The core Torii MCP gateway.

    Responsibilities:
    - Convert configured REST APIs into MCP tools
    - Aggregate tools from upstream MCP servers
    - Run workflow definitions as callable tools
    - Expose everything as a unified MCP server
    """

    def __init__(self, config: ToriiConfig) -> None:
        self.config = config
        self.server = Server(config.server.name)

        self._api_tools: dict[str, APITool] = {}
        self._aggregator = MCPAggregator()
        self._workflow_engine = WorkflowEngine(self)

        self._register_handlers()

    def _register_handlers(self) -> None:
        """Wire up MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools(request: ListToolsRequest) -> ListToolsResult:
            return ListToolsResult(tools=self._all_tool_definitions())

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            result = await self._dispatch(request.params.name, dict(request.params.arguments or {}))
            return CallToolResult(content=[TextContent(type="text", text=result)])

    def _all_tool_definitions(self) -> list[Tool]:
        """Collect tool definitions from all sources."""
        tools: list[Tool] = []

        # 1. API-converted tools
        for tool in self._api_tools.values():
            tools.append(Tool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.input_schema,
            ))

        # 2. Aggregated MCP server tools
        for remote in self._aggregator.tools:
            tools.append(Tool(
                name=remote.name,
                description=remote.description,
                inputSchema=remote.input_schema,
            ))

        # 3. Workflow tools
        for wf in self.config.workflows:
            tools.append(Tool(
                name=f"workflow_{wf.name.replace('-', '_')}",
                description=wf.description or f"Run the '{wf.name}' workflow",
                inputSchema={"type": "object", "properties": {}},
            ))

        return tools

    async def _dispatch(self, name: str, params: dict[str, Any]) -> str:
        """Route a tool call to the right handler."""
        # API tool?
        if name in self._api_tools:
            return await self._api_tools[name].call(params)

        # Workflow tool?
        if name.startswith("workflow_"):
            wf_name = name[len("workflow_"):].replace("_", "-")
            return await self._workflow_engine.run(wf_name, params)

        # Aggregated MCP tool?
        result = await self._aggregator.call_tool(name, params)
        return result

    async def call_tool(self, name: str, params: dict[str, Any]) -> str:
        """Public interface used by the WorkflowEngine."""
        return await self._dispatch(name, params)

    async def startup(self) -> None:
        """Initialize all API tools and connect to upstream MCP servers."""
        converter = APIConverter()

        # Register API tools
        for api_cfg in self.config.apis:
            tools = converter.convert(api_cfg)
            for tool in tools:
                self._api_tools[tool.name] = tool
            logger.info(f"[api] '{api_cfg.name}' → {len(tools)} tools registered")

        # Register and connect MCP servers
        for srv_cfg in self.config.mcp_servers:
            self._aggregator.add_server(srv_cfg)

        await self._aggregator.connect_all()

        # Register workflows
        for wf in self.config.workflows:
            self._workflow_engine.register(wf)

        total = len(self._all_tool_definitions())
        logger.info(f"⛩️  Torii ready — {total} tools available")

    async def shutdown(self) -> None:
        """Clean up connections."""
        await self._aggregator.disconnect_all()

    def get_initialization_options(self) -> InitializationOptions:
        return InitializationOptions(
            server_name=self.config.server.name,
            server_version="0.1.0",
            capabilities=self.server.get_capabilities(
                notification_options=None,
                experimental_capabilities={},
            ),
        )
