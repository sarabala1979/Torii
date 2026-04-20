# Changelog

All notable changes to Torii will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- Python project scaffold with `pyproject.toml`
- `torii.config` — Pydantic v2 config models with env var expansion (`${VAR}`)
- `torii.api` — REST API → MCP tool converter (`APIConverter`, `APITool`)
- `torii.mcp.aggregator` — HTTP and stdio upstream MCP server aggregation
- `torii.mcp.gateway` — Core `ToriiGateway` MCP server using the MCP Python SDK
- `torii.workflow` — `WorkflowEngine` with `{{step.output}}` template resolution
- `torii.cli` — Typer CLI: `serve`, `validate`, `tools list`, `version`
- Unit tests for config, converter, and workflow engine
- GitHub Actions CI: test matrix (Python 3.11/3.12), lint, type check, PyPI publish
- Pre-commit hooks with Ruff and standard checks
- `examples/torii.config.yaml` — fully annotated example
- `docs/getting-started.md` — step-by-step guide
