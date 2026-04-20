"""
Config parsing and validation for torii.config.yaml
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# Matches ${VAR_NAME} patterns in config values
_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _expand_env(value: str) -> str:
    """Replace ${VAR} placeholders with environment variable values."""
    return _ENV_VAR_RE.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)


def _expand_env_in_dict(data: Any) -> Any:
    """Recursively expand env vars in a parsed YAML structure."""
    if isinstance(data, str):
        return _expand_env(data)
    if isinstance(data, dict):
        return {k: _expand_env_in_dict(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_expand_env_in_dict(item) for item in data]
    return data


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

class AuthConfig(BaseModel):
    type: Literal["api_key", "bearer", "basic", "oauth2", "none"] = "none"
    header: str = "Authorization"
    value: str = ""
    token: str = ""  # alias for bearer token

    def get_headers(self) -> dict[str, str]:
        """Return the HTTP headers needed for this auth config."""
        match self.type:
            case "bearer":
                t = self.token or self.value
                return {"Authorization": f"Bearer {t}"}
            case "api_key":
                return {self.header: self.value}
            case "basic":
                import base64
                encoded = base64.b64encode(f"{self.header}:{self.value}".encode()).decode()
                return {"Authorization": f"Basic {encoded}"}
            case _:
                return {}


# ─────────────────────────────────────────────
# API → MCP Conversion
# ─────────────────────────────────────────────

class ParameterConfig(BaseModel):
    name: str
    in_: Literal["path", "query", "body"] = Field("query", alias="in")
    description: str = ""
    required: bool = False
    type: Literal["string", "integer", "number", "boolean", "object", "array"] = "string"
    default: Any = None

    model_config = {"populate_by_name": True}


class EndpointConfig(BaseModel):
    path: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    tool_name: str
    description: str = ""
    parameters: list[ParameterConfig] = []

    @field_validator("method")
    @classmethod
    def uppercase_method(cls, v: str) -> str:
        return v.upper()

    @field_validator("tool_name")
    @classmethod
    def valid_tool_name(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(f"tool_name '{v}' must be lowercase snake_case")
        return v


class APIConfig(BaseModel):
    name: str
    base_url: str
    auth: AuthConfig = AuthConfig()
    headers: dict[str, str] = {}
    endpoints: list[EndpointConfig] = []

    @field_validator("base_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


# ─────────────────────────────────────────────
# MCP Aggregation
# ─────────────────────────────────────────────

class MCPServerConfig(BaseModel):
    name: str
    url: str = ""           # for HTTP/SSE servers
    command: str = ""       # for stdio servers (e.g. "npx")
    args: list[str] = []
    env: dict[str, str] = {}
    auth: AuthConfig = AuthConfig()
    namespace: str = ""     # prefix for tool names, e.g. "gh" → "gh.list_repos"

    @model_validator(mode="after")
    def must_have_url_or_command(self) -> MCPServerConfig:
        if not self.url and not self.command:
            raise ValueError(f"mcp_server '{self.name}' must have either 'url' or 'command'")
        return self


# ─────────────────────────────────────────────
# Workflow Engine
# ─────────────────────────────────────────────

class StepConfig(BaseModel):
    id: str
    tool: str
    input: dict[str, Any] = {}


class WorkflowConfig(BaseModel):
    name: str
    description: str = ""
    steps: list[StepConfig] = []


# ─────────────────────────────────────────────
# Server
# ─────────────────────────────────────────────

class ServerConfig(BaseModel):
    port: int = 8080
    name: str = "Torii Gateway"
    host: str = "0.0.0.0"


# ─────────────────────────────────────────────
# Root Config
# ─────────────────────────────────────────────

class ToriiConfig(BaseModel):
    server: ServerConfig = ServerConfig()
    apis: list[APIConfig] = []
    mcp_servers: list[MCPServerConfig] = []
    workflows: list[WorkflowConfig] = []

    @classmethod
    def load(cls, path: str | Path) -> "ToriiConfig":
        """Load and validate a torii.config.yaml file."""
        raw = Path(path).read_text()
        data = yaml.safe_load(raw)
        data = _expand_env_in_dict(data or {})
        return cls.model_validate(data)

    def get_api(self, name: str) -> APIConfig | None:
        return next((a for a in self.apis if a.name == name), None)

    def get_workflow(self, name: str) -> WorkflowConfig | None:
        return next((w for w in self.workflows if w.name == name), None)
