# ⛩️ Torii

> **The MCP gateway that turns any API into a tool — and unifies all your MCP servers into one.**

[![CI](https://github.com/sarabala1979/Torii/actions/workflows/ci.yml/badge.svg)](https://github.com/sarabala1979/Torii/actions)
[![PyPI](https://img.shields.io/pypi/v/torii)](https://pypi.org/project/torii/)
[![Python](https://img.shields.io/pypi/pyversions/torii)](https://pypi.org/project/torii/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/sarabala1979/Torii/pulls)

---

## What is Torii?

**Torii** (鳥居) is a sacred gateway in Japanese architecture — everything passes *through* it. Just as a torii gate marks the threshold into something greater, **Torii the project** is the gateway between your APIs, MCP servers, and AI assistants.

Torii is an open-source **MCP (Model Context Protocol) gateway** written in Python that solves three core problems:

| Problem | Torii's Solution |
|---|---|
| "My REST APIs aren't accessible to AI tools" | **Dynamic API → MCP conversion** — point Torii at any endpoint, get instant MCP tools |
| "I have too many MCP servers to manage" | **MCP aggregation** — merge multiple servers into a single unified endpoint |
| "I need to orchestrate multi-step AI workflows" | **Workflow engine** — chain tools together with declarative config |

---

## ✨ Features

- **🔄 Dynamic API → MCP Conversion** — any REST endpoint becomes an MCP tool, zero code required
- **🔗 MCP Aggregation** — connect multiple MCP servers (HTTP or stdio) through one gateway
- **⚙️ Workflow Engine** — chain tools with `{{step.output}}` template variables
- **🔒 Auth Support** — bearer, API key, basic auth — forwarded automatically
- **🌍 Env Var Expansion** — use `${MY_SECRET}` in config, never hardcode credentials
- **🚀 Zero Code** — everything driven by `torii.config.yaml`
- **📊 Rich CLI** — beautiful terminal output with `torii serve`, `validate`, `tools list`

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│          AI Assistant / MCP Client           │
│       (Claude, Cursor, Windsurf, etc.)       │
└──────────────────┬───────────────────────────┘
                   │  MCP Protocol
                   ▼
┌──────────────────────────────────────────────┐
│               ⛩️  TORII                       │
│                                              │
│  ┌─────────────┐    ┌─────────────────────┐  │
│  │  API → MCP  │    │   MCP Aggregator    │  │
│  │  Converter  │    │  (multi-server hub) │  │
│  └──────┬──────┘    └──────────┬──────────┘  │
│         │                      │             │
│  ┌──────▼──────────────────────▼──────────┐  │
│  │           Workflow Engine              │  │
│  │   (chain tools, template variables)   │  │
│  └────────────────────────────────────────┘  │
└────────────┬──────────────────┬──────────────┘
             │                  │
   ┌──────────▼──────┐  ┌───────▼─────────────┐
   │  Your REST APIs │  │  Upstream MCP Servers│
   │  (any endpoint) │  │  (GitHub, Slack, ...) │
   └─────────────────┘  └─────────────────────┘
```

---

## 🚀 Quick Start

### Install

```bash
pip install torii
```

### Create a config

```yaml
# torii.config.yaml
server:
  port: 8080

apis:
  - name: "weather"
    base_url: "https://api.openweathermap.org/data/2.5"
    auth:
      type: "api_key"
      header: "X-API-Key"
      value: "${WEATHER_API_KEY}"
    endpoints:
      - path: "/weather"
        method: GET
        tool_name: "get_current_weather"
        description: "Get current weather for a city"
        parameters:
          - name: "q"
            in: query
            description: "City name"
            required: true
            type: string

mcp_servers:
  - name: "github"
    url: "https://api.githubcopilot.com/mcp/"
    auth:
      type: "bearer"
      token: "${GITHUB_TOKEN}"
    namespace: "gh"

workflows:
  - name: "daily-standup"
    description: "Fetch open PRs and post to Slack"
    steps:
      - id: "fetch_prs"
        tool: "gh.list_pull_requests"
        input:
          state: "open"
      - id: "notify"
        tool: "slack.post_message"
        input:
          channel: "#standup"
          message: "Open PRs: {{fetch_prs.output}}"
```

### Start the gateway

```bash
WEATHER_API_KEY=your_key GITHUB_TOKEN=your_token torii serve
```

```
⛩️  Torii — My Torii Gateway
   Config:    torii.config.yaml
   Endpoint:  http://0.0.0.0:8080/mcp
   APIs:      1
   MCP Servers: 1
   Workflows: 1

✓ Gateway ready — listening for MCP connections
```

### Connect to Claude Desktop

```json
{
  "mcpServers": {
    "torii": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

---

## 📖 Configuration Reference

### API Conversion

```yaml
apis:
  - name: "my-api"
    base_url: "https://api.example.com/v1"
    auth:
      type: "bearer"          # bearer | api_key | basic | none
      token: "${API_TOKEN}"
    headers:
      X-Client: "torii"
    endpoints:
      - path: "/users/{id}"
        method: GET           # GET | POST | PUT | PATCH | DELETE
        tool_name: "get_user" # snake_case, exposed as MCP tool name
        description: "Fetch a user by ID"
        parameters:
          - name: "id"
            in: path          # path | query | body
            required: true
            type: string
```

### MCP Aggregation

```yaml
mcp_servers:
  # Remote HTTP server
  - name: "github"
    url: "https://api.githubcopilot.com/mcp/"
    auth:
      type: bearer
      token: "${GITHUB_TOKEN}"
    namespace: "gh"           # tools become gh.list_repos, etc.

  # Local stdio server
  - name: "filesystem"
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    namespace: "fs"
```

### Workflow Engine

```yaml
workflows:
  - name: "create-and-notify"
    description: "Create a GitHub issue then post to Slack"
    steps:
      - id: "create"
        tool: "gh.create_issue"
        input:
          title: "{{input.title}}"
          body: "{{input.body}}"

      - id: "notify"
        tool: "slack.post_message"
        input:
          channel: "#engineering"
          message: "Issue created: {{create.output}}"
```

Templates support `{{step_id.output}}` and `{{input.field}}` syntax.

---

## 🔌 Connecting AI Assistants

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "torii": { "url": "http://localhost:8080/mcp" }
  }
}
```

### Cursor

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "torii": { "url": "http://localhost:8080/mcp" }
  }
}
```

### VS Code (Copilot)

`.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "torii": { "type": "http", "url": "http://localhost:8080/mcp" }
  }
}
```

---

## 🛠️ CLI Reference

```bash
# Start the gateway
torii serve [--config torii.config.yaml] [--port 8080]

# Validate config without starting
torii validate [--config torii.config.yaml]

# List all tools that will be exposed
torii tools list [--config torii.config.yaml]

# Show version
torii version
```

---

## 🐳 Docker

```bash
docker run -p 8080:8080 \
  -v $(pwd)/torii.config.yaml:/app/torii.config.yaml \
  -e GITHUB_TOKEN=your_token \
  ghcr.io/sarabala1979/torii:latest
```

```yaml
# docker-compose.yml
services:
  torii:
    image: ghcr.io/sarabala1979/torii:latest
    ports:
      - "8080:8080"
    volumes:
      - ./torii.config.yaml:/app/torii.config.yaml
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    restart: unless-stopped
```

---

## 🗺️ Roadmap

- [x] Dynamic API → MCP conversion
- [x] Multi-MCP server aggregation
- [x] Workflow engine with template variables
- [x] Bearer / API key / basic auth support
- [x] Env var expansion in config
- [ ] OpenAPI / Swagger spec auto-import
- [ ] Web UI dashboard
- [ ] GraphQL support
- [ ] Tool-level rate limiting & caching
- [ ] Audit logging
- [ ] Docker image on GHCR

---

## 🤝 Contributing

We welcome all contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

```bash
git clone https://github.com/sarabala1979/Torii.git
cd Torii
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/unit/ -v
```

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

⛩️ **[Docs](docs/getting-started.md)** · **[Examples](examples/)** · **[Issues](https://github.com/sarabala1979/Torii/issues)** · **[Discussions](https://github.com/sarabala1979/Torii/discussions)**

*Configure once. Connect everything.*

</div>
