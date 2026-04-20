"""
MCP Aggregator — connects to multiple upstream MCP servers
and proxies their tools through a single Torii endpoint.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from torii.config import MCPServerConfig

logger = logging.getLogger(__name__)


@dataclass
class RemoteTool:
    """Represents a tool discovered from an upstream MCP server."""
    name: str                        # namespaced name, e.g. "gh.list_repos"
    original_name: str               # original name from the upstream server
    description: str
    input_schema: dict[str, Any]
    server: "MCPServer"


@dataclass
class MCPServer:
    """Represents a connected upstream MCP server."""
    config: MCPServerConfig
    tools: list[RemoteTool] = field(default_factory=list)
    _connected: bool = False

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def namespace(self) -> str:
        return self.config.namespace

    def tool_name(self, original: str) -> str:
        """Apply namespace prefix to a tool name."""
        if self.namespace:
            return f"{self.namespace}.{original}"
        return original


class HTTPMCPServer(MCPServer):
    """
    Connects to a remote MCP server over HTTP/SSE.
    Discovers tools via the MCP initialize + tools/list protocol.
    """

    async def connect(self) -> None:
        """Connect and discover all tools from the remote server."""
        try:
            headers = self.config.auth.get_headers()
            async with httpx.AsyncClient(timeout=15.0) as client:
                # MCP initialize handshake
                init_resp = await client.post(
                    self.config.url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "torii", "version": "0.1.0"},
                        },
                    },
                    headers={"Content-Type": "application/json", **headers},
                )
                init_resp.raise_for_status()

                # List available tools
                tools_resp = await client.post(
                    self.config.url,
                    json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                    headers={"Content-Type": "application/json", **headers},
                )
                tools_resp.raise_for_status()
                data = tools_resp.json()
                raw_tools = data.get("result", {}).get("tools", [])

            self.tools = [
                RemoteTool(
                    name=self.tool_name(t["name"]),
                    original_name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server=self,
                )
                for t in raw_tools
            ]
            self._connected = True
            logger.info(f"[{self.name}] Connected — {len(self.tools)} tools discovered")

        except Exception as e:
            logger.warning(f"[{self.name}] Failed to connect: {e}")

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> str:
        """Call a tool on the remote MCP server."""
        headers = self.config.auth.get_headers()
        headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.config.url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": params},
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result", {})
        content = result.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", json.dumps(result))
        return json.dumps(result)


class StdioMCPServer(MCPServer):
    """
    Connects to a local MCP server over stdio (e.g. npx, python -m ...).
    Spawns the subprocess and communicates via JSON-RPC over stdin/stdout.
    """

    _process: asyncio.subprocess.Process | None = None
    _msg_id: int = 0

    async def connect(self) -> None:
        """Spawn the subprocess and discover tools."""
        try:
            env = {**__import__("os").environ, **self.config.env}
            self._process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # Initialize
            await self._send({"method": "initialize", "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "torii", "version": "0.1.0"},
            }})

            # List tools
            result = await self._send({"method": "tools/list", "params": {}})
            raw_tools = result.get("tools", [])

            self.tools = [
                RemoteTool(
                    name=self.tool_name(t["name"]),
                    original_name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server=self,
                )
                for t in raw_tools
            ]
            self._connected = True
            logger.info(f"[{self.name}] Connected (stdio) — {len(self.tools)} tools")

        except Exception as e:
            logger.warning(f"[{self.name}] Failed to start: {e}")

    async def _send(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a JSON-RPC message and read the response."""
        self._msg_id += 1
        msg = json.dumps({"jsonrpc": "2.0", "id": self._msg_id, **payload}) + "\n"

        assert self._process and self._process.stdin and self._process.stdout
        self._process.stdin.write(msg.encode())
        await self._process.stdin.drain()

        line = await asyncio.wait_for(self._process.stdout.readline(), timeout=10.0)
        data = json.loads(line)
        return data.get("result", {})

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> str:
        result = await self._send({
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params},
        })
        content = result.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", json.dumps(result))
        return json.dumps(result)

    async def disconnect(self) -> None:
        if self._process:
            self._process.terminate()
            await self._process.wait()


class MCPAggregator:
    """
    Aggregates multiple MCP servers into a single unified tool registry.
    Connects to all configured servers and exposes their tools as one flat list.
    """

    def __init__(self) -> None:
        self._servers: list[MCPServer] = []

    def add_server(self, cfg: MCPServerConfig) -> None:
        """Register an upstream MCP server."""
        if cfg.url:
            self._servers.append(HTTPMCPServer(config=cfg))
        elif cfg.command:
            self._servers.append(StdioMCPServer(config=cfg))

    async def connect_all(self) -> None:
        """Connect to all registered MCP servers concurrently."""
        await asyncio.gather(*(srv.connect() for srv in self._servers))

    @property
    def tools(self) -> list[RemoteTool]:
        """Return all tools from all connected servers."""
        result = []
        for srv in self._servers:
            result.extend(srv.tools)
        return result

    def get_tool(self, name: str) -> RemoteTool | None:
        """Look up a tool by its namespaced name."""
        return next((t for t in self.tools if t.name == name), None)

    async def call_tool(self, name: str, params: dict[str, Any]) -> str:
        """Call a tool by its namespaced name."""
        tool = self.get_tool(name)
        if not tool:
            return f"Error: tool '{name}' not found"

        srv = tool.server
        if isinstance(srv, HTTPMCPServer):
            return await srv.call_tool(tool.original_name, params)
        if isinstance(srv, StdioMCPServer):
            return await srv.call_tool(tool.original_name, params)
        return "Error: unknown server type"

    async def disconnect_all(self) -> None:
        for srv in self._servers:
            if isinstance(srv, StdioMCPServer):
                await srv.disconnect()
