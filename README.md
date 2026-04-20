# ⛩️ Torii

> **The MCP gateway that turns any API into a tool — and unifies all your MCP servers into one.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Go Report Card](https://goreportcard.com/badge/github.com/sarabala1979/Torii)](https://goreportcard.com/report/github.com/sarabala1979/Torii)
[![GitHub Stars](https://img.shields.io/github/stars/sarabala1979/Torii?style=social)](https://github.com/sarabala1979/Torii/stargazers)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/sarabala1979/Torii/pulls)

---

## What is Torii?

**Torii** (鳥居) is a sacred gateway in Japanese architecture — a passage through which everything must flow. Just as a torii gate marks the threshold between the ordinary world and something greater, **Torii the project** is the gateway between your APIs, MCP servers, and AI assistants.

Torii is an open-source **MCP (Model Context Protocol) gateway** that solves three critical problems:

| Problem | Torii's Solution |
|---|---|
| "My REST APIs aren't accessible to AI tools" | **Dynamic API → MCP conversion**: Point Torii at any API, get instant MCP tools |
| "I have too many MCP servers to manage" | **MCP aggregation**: Merge multiple MCP servers into a single unified endpoint |
| "I need to orchestrate complex tool workflows" | **Workflow configuration**: Chain tools together with declarative config |

---

## ✨ Features

- **🔄 Dynamic API → MCP Conversion** — Point Torii at any REST/HTTP endpoint and it instantly becomes an MCP tool, no code required
- **🔗 MCP Aggregation** — Connect multiple MCP servers and expose them as a single unified MCP endpoint
- **⚙️ Workflow Configuration** — Define complex multi-step tool chains with a simple config file
- **🚀 Zero Code Required** — Everything configurable via `torii.config.yaml`
- **🔌 Hot Reload** — Add or remove APIs and MCP servers without restarting
- **🔒 Auth Support** — Forward authentication headers to upstream APIs automatically
- **📊 Observability** — Built-in logging, tracing, and health checks

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           AI Assistant / MCP Client          │
│        (Claude, Cursor, Windsurf, etc.)      │
└───────────────────┬─────────────────────────┘
                    │  MCP Protocol
                    ▼
┌─────────────────────────────────────────────┐
│                ⛩️  TORII                      │
│                                             │
│  ┌─────────────┐    ┌────────────────────┐  │
│  │  API → MCP  │    │  MCP Aggregator    │  │
│  │  Converter  │    │  (Multi-server hub) │  │
│  └──────┬──────┘    └────────┬───────────┘  │
│         │                    │              │
│  ┌──────▼────────────────────▼───────────┐  │
│  │         Workflow Engine               │  │
│  │    (Chain tools, configure flows)     │  │
│  └───────────────────────────────────────┘  │
└────────────┬────────────────┬───────────────┘
             │                │
    ┌────────▼──────┐  ┌──────▼──────────────┐
    │  Your REST    │  │  Other MCP Servers   │
    │  APIs         │  │  (GitHub, Slack, etc)│
    └───────────────┘  └─────────────────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
# Using Go
go install github.com/sarabala1979/Torii@latest

# Using Docker
docker pull ghcr.io/sarabala1979/torii:latest

# Using Homebrew (macOS)
brew install sarabala1979/tap/torii
```

### Basic Usage

**1. Create a config file** (`torii.config.yaml`):

```yaml
server:
  port: 8080
  name: "My Torii Gateway"

# Convert REST APIs to MCP tools
apis:
  - name: "weather-api"
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
            description: "City name"
            required: true

# Aggregate other MCP servers
mcp_servers:
  - name: "github"
    url: "https://api.githubcopilot.com/mcp/"
    auth:
      type: "bearer"
      token: "${GITHUB_TOKEN}"
  - name: "slack"
    command: "npx @slack/mcp-server"

# Define workflows
workflows:
  - name: "daily-standup"
    description: "Fetch GitHub PRs and post to Slack"
    steps:
      - tool: "github.list_pull_requests"
        output: "prs"
      - tool: "slack.post_message"
        input:
          channel: "#standup"
          message: "Today's PRs: {{prs}}"
```

**2. Start Torii:**

```bash
torii serve --config torii.config.yaml
```

**3. Connect your AI assistant:**

```json
{
  "mcpServers": {
    "torii": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

That's it — all your APIs and MCP servers are now accessible through a single gateway. ⛩️

---

## 📖 Configuration Reference

### API Conversion

```yaml
apis:
  - name: "my-api"
    base_url: "https://api.example.com/v1"
    
    # Authentication options
    auth:
      type: "api_key" | "bearer" | "basic" | "oauth2" | "none"
      header: "Authorization"         # for api_key/bearer
      value: "${MY_API_KEY}"          # supports env vars
    
    # Headers forwarded to all endpoints
    headers:
      Content-Type: "application/json"
      X-Client: "torii"
    
    endpoints:
      - path: "/users/{id}"
        method: GET
        tool_name: "get_user"
        description: "Fetch a user by ID"
        parameters:
          - name: "id"
            in: "path"           # path | query | body
            description: "User ID"
            required: true
            type: "string"
```

### MCP Aggregation

```yaml
mcp_servers:
  # Remote MCP server (HTTP)
  - name: "remote-server"
    url: "https://mcp.example.com/mcp"
    auth:
      type: "bearer"
      token: "${MCP_TOKEN}"
  
  # Local MCP server (stdio)
  - name: "local-server"
    command: "npx my-mcp-server"
    args: ["--port", "3000"]
    env:
      API_KEY: "${MY_KEY}"
  
  # Tool namespace (avoid collisions)
  - name: "github"
    url: "https://api.githubcopilot.com/mcp/"
    namespace: "gh"    # tools become gh.list_repos, gh.create_issue, etc.
```

### Workflow Engine

```yaml
workflows:
  - name: "create-github-issue-from-slack"
    trigger: "on_tool_call"        # manual | on_tool_call | scheduled
    steps:
      - id: "parse"
        tool: "extract_issue_details"
        input:
          text: "{{trigger.input}}"
        
      - id: "create"
        tool: "github.create_issue"
        input:
          title: "{{parse.output.title}}"
          body: "{{parse.output.body}}"
          labels: ["{{parse.output.priority}}"]
        
      - id: "notify"
        tool: "slack.post_message"
        input:
          channel: "#engineering"
          message: "Issue created: {{create.output.html_url}}"
```

---

## 🔌 Connecting to AI Assistants

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "torii": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "torii": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### VS Code (Copilot)

Add to `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "torii": {
      "type": "http",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

---

## 🐳 Docker

```bash
# Run with Docker
docker run -p 8080:8080 \
  -v $(pwd)/torii.config.yaml:/config/torii.config.yaml \
  -e GITHUB_TOKEN=your_token \
  ghcr.io/sarabala1979/torii:latest

# Docker Compose
```

```yaml
# docker-compose.yml
version: "3.8"
services:
  torii:
    image: ghcr.io/sarabala1979/torii:latest
    ports:
      - "8080:8080"
    volumes:
      - ./torii.config.yaml:/config/torii.config.yaml
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - SLACK_TOKEN=${SLACK_TOKEN}
    restart: unless-stopped
```

---

## 🛠️ CLI Reference

```bash
# Start the gateway
torii serve [--config path/to/config.yaml] [--port 8080]

# Validate your config
torii validate --config torii.config.yaml

# List all registered tools
torii tools list

# Test a specific tool
torii tools invoke get_current_weather --params '{"q": "San Francisco"}'

# Import an OpenAPI spec and auto-generate config
torii import openapi --spec api.yaml --output torii.config.yaml

# Check gateway health
torii health
```

---

## 📦 Use Cases

**For Developers**
- Instantly expose any internal REST API to Claude, Cursor, or Copilot
- Replace complex multi-server MCP setups with a single gateway
- Build multi-step AI workflows without writing glue code

**For Teams**
- Standardize AI tool access across your organization
- Add auth, rate limiting, and observability to all AI tool calls
- One config file, one endpoint — easy to share and version-control

**For Enterprises**
- Centralized control plane for all MCP access
- Audit trail for every AI tool invocation
- Fine-grained access control per team or service

---

## 🗺️ Roadmap

- [x] Dynamic API → MCP conversion
- [x] Multi-MCP aggregation
- [x] Workflow configuration engine
- [ ] Web UI for managing tools and workflows
- [ ] OpenAPI / Swagger auto-import
- [ ] GraphQL support
- [ ] gRPC support
- [ ] Tool-level rate limiting
- [ ] Audit logging
- [ ] Torii Cloud (hosted gateway)

---

## 🤝 Contributing

We welcome contributions of all kinds! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

```bash
# Clone the repo
git clone https://github.com/sarabala1979/Torii.git
cd Torii

# Install dependencies
go mod download

# Run tests
go test ./...

# Start in development mode
go run main.go serve --config examples/torii.config.yaml
```

---

## 📄 License

Torii is open-source software licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

Named after the iconic **torii gate** (鳥居) of Japanese Shinto shrines — a sacred threshold between worlds. Just as the torii marks the passage into a sacred space, this project marks the gateway between your tools and AI.

---

<div align="center">

⛩️ **[Documentation](https://torii.dev)** · **[Changelog](CHANGELOG.md)** · **[Issues](https://github.com/sarabala1979/Torii/issues)** · **[Discussions](https://github.com/sarabala1979/Torii/discussions)**

*Configure once. Connect everything.*

</div>
