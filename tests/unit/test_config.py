"""Tests for config parsing and validation."""

import os
import textwrap
from pathlib import Path

import pytest

from torii.config import ToriiConfig, AuthConfig


class TestAuthConfig:
    def test_bearer_headers(self):
        auth = AuthConfig(type="bearer", token="my-token")
        assert auth.get_headers() == {"Authorization": "Bearer my-token"}

    def test_api_key_headers(self):
        auth = AuthConfig(type="api_key", header="X-API-Key", value="secret")
        assert auth.get_headers() == {"X-API-Key": "secret"}

    def test_none_returns_empty(self):
        auth = AuthConfig(type="none")
        assert auth.get_headers() == {}


class TestToriiConfig:
    def test_load_minimal(self, tmp_path: Path):
        cfg_file = tmp_path / "torii.config.yaml"
        cfg_file.write_text(textwrap.dedent("""\
            server:
              port: 9090
              name: Test Gateway
        """))
        cfg = ToriiConfig.load(cfg_file)
        assert cfg.server.port == 9090
        assert cfg.server.name == "Test Gateway"
        assert cfg.apis == []
        assert cfg.mcp_servers == []

    def test_load_api_config(self, tmp_path: Path):
        cfg_file = tmp_path / "torii.config.yaml"
        cfg_file.write_text(textwrap.dedent("""\
            apis:
              - name: weather
                base_url: https://api.weather.com
                endpoints:
                  - path: /current
                    method: GET
                    tool_name: get_weather
                    description: Get current weather
                    parameters:
                      - name: city
                        in: query
                        required: true
                        type: string
        """))
        cfg = ToriiConfig.load(cfg_file)
        assert len(cfg.apis) == 1
        api = cfg.apis[0]
        assert api.name == "weather"
        assert api.base_url == "https://api.weather.com"
        assert len(api.endpoints) == 1
        ep = api.endpoints[0]
        assert ep.tool_name == "get_weather"
        assert ep.method == "GET"

    def test_env_var_expansion(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("MY_SECRET", "abc123")
        cfg_file = tmp_path / "torii.config.yaml"
        cfg_file.write_text(textwrap.dedent("""\
            apis:
              - name: my-api
                base_url: https://api.example.com
                auth:
                  type: bearer
                  token: ${MY_SECRET}
        """))
        cfg = ToriiConfig.load(cfg_file)
        assert cfg.apis[0].auth.token == "abc123"

    def test_base_url_strips_trailing_slash(self, tmp_path: Path):
        cfg_file = tmp_path / "torii.config.yaml"
        cfg_file.write_text(textwrap.dedent("""\
            apis:
              - name: api
                base_url: https://api.example.com/v1/
        """))
        cfg = ToriiConfig.load(cfg_file)
        assert cfg.apis[0].base_url == "https://api.example.com/v1"

    def test_mcp_server_requires_url_or_command(self, tmp_path: Path):
        cfg_file = tmp_path / "torii.config.yaml"
        cfg_file.write_text(textwrap.dedent("""\
            mcp_servers:
              - name: bad-server
        """))
        with pytest.raises(Exception, match="url.*command"):
            ToriiConfig.load(cfg_file)

    def test_default_server_port(self, tmp_path: Path):
        cfg_file = tmp_path / "torii.config.yaml"
        cfg_file.write_text("{}\n")
        cfg = ToriiConfig.load(cfg_file)
        assert cfg.server.port == 8080
