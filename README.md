<div align="center">


# ⛩️ Torii

### The MCP Gateway for the AI-Native Era

**Turn any REST API into an MCP tool in seconds.**  
**Unify every MCP server behind a single endpoint.**  
**Orchestrate multi-step AI workflows with pure YAML.**

<br/>

[![CI](https://github.com/sarabala1979/Torii/actions/workflows/ci.yml/badge.svg)](https://github.com/sarabala1979/Torii/actions)
[![PyPI](https://img.shields.io/pypi/v/torii?color=red&label=pypi)](https://pypi.org/project/torii/)
[![Python](https://img.shields.io/pypi/pyversions/torii?color=blue)](https://pypi.org/project/torii/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/sarabala1979/Torii/pulls)
[![Stars](https://img.shields.io/github/stars/sarabala1979/Torii?style=social)](https://github.com/sarabala1979/Torii/stargazers)

<br/>

```bash
pip install torii && torii serve
```

*One command. Every tool. Connected.*

</div>

---

## The Problem

The AI tooling landscape is fragmented. You have:

- **Dozens of REST APIs** your AI can't touch — because they speak HTTP, not MCP
- **Multiple MCP servers** scattered across your stack — each needing its own config, auth, and client
- **No way to chain tools together** — every multi-step workflow requires custom code

You end up writing glue code. Lots of it. Or worse — your AI assistant sits idle, cut off from the very systems it should be automating.

**Torii fixes this.**

---

## The Solution

Torii is an open-source **MCP (Model Context Protocol) gateway** that acts as the universal adapter between your existing infrastructure and any AI assistant — Claude, Cursor, Windsurf, VS Code Copilot, and more.

```
Your APIs  ──┐
              ├──▶  ⛩️ Torii  ──▶  Claude / Cursor / Windsurf
MCP Servers ──┘
```

Point Torii at your APIs and MCP servers. Write a YAML config. Start the gateway. Your AI now has access to everything — through a single, unified MCP endpoint.

No SDK. No code. No boilerplate.

---

## What Torii Does

### 🔄 API → MCP Conversion

Any REST endpoint becomes an MCP tool — automatically. Torii reads your config, generates a proper JSON Schema for each parameter, handles authentication, and exposes the endpoint as a first-class MCP tool.

```yaml
apis:
  - name: "stripe"
    base_url: "https://api.stripe.com/v1"
    auth:
      type: bearer
      token: "${STRIPE_SECRET_KEY}"
    endpoints:
      - path: "/customers/{id}"
        method: GET
        tool_name: "get_customer"
        description: "Fetch a Stripe customer by ID"
        parameters:
          - name: id
            in: path
            required: true
            type: string
```

Ask Claude: *"Look up Stripe customer cus_abc123"* — it just works.

---

### 🔗 MCP Aggregation

Running GitHub MCP, Slack MCP, filesystem MCP, and three internal servers? Torii connects to all of them and surfaces their tools through **one endpoint**. No more managing N different MCP configs. Namespacing prevents tool name collisions automatically.

```yaml
mcp_servers:
  - name: github
    url: "https://api.githubcopilot.com/mcp/"
    auth: { type: bearer, token: "${GITHUB_TOKEN}" }
    namespace: gh          # → gh.list_repos, gh.create_issue

  - name: slack
    command: npx
    args: ["-y", "@slack/mcp-server"]
    namespace: slack       # → slack.post_message, slack.search

  - name: internal-db
    command: python
    args: ["-m", "my_mcp_server"]
    namespace: db          # → db.query, db.insert
```

One MCP config in Claude Desktop. Every tool available.

---

### ⚙️ Workflow Engine

Chain tools together into reusable, declarative workflows. Pass outputs from one step as inputs to the next using `{{step_id.output}}` templates. Torii runs the whole sequence as a single callable MCP tool.

```yaml
workflows:
  - name: "triage-and-notify"
    description: "Create a GitHub issue from a bug report and alert the team"
    steps:
      - id: create_issue
        tool: gh.create_issue
        input:
          title: "{{input.title}}"
          body: "{{input.description}}"
          labels: ["bug", "{{input.priority}}"]

      - id: notify_team
        tool: slack.post_message
        input:
          channel: "#engineering"
          message: "🐛 New issue: <{{create_issue.output.url}}|{{input.title}}>"

      - id: assign_oncall
        tool: gh.add_assignee
        input:
          issue_number: "{{create_issue.output.number}}"
          assignee: "{{input.oncall}}"
```

Tell Claude: *"Triage this bug report and notify the team"* — three tools fire in sequence, automatically.

---

## Quickstart

### 1. Install

```bash
pip install torii
```

### 2. Create `torii.config.yaml`

```yaml
server:
  port: 8080
  name: "My AI Gateway"

apis:
  - name: "jsonplaceholder"
    base_url: "https://jsonplaceholder.typicode.com"
    endpoints:
      - path: "/posts/{id}"
        method: GET
        tool_name: "get_post"
        description: "Fetch a blog post by ID"
        parameters:
          - name: id
            in: path
            required: true
            type: string

      - path: "/posts"
        method: POST
        tool_name: "create_post"
        description: "Create a new blog post"
        parameters:
          - name: title
            in: body
            required: true
            type: string
          - name: body
            in: body
            required: true
            type: string
```

### 3. Start Torii

```bash
torii serve
```

```
⛩️  Torii — My AI Gateway
   Endpoint:  http://localhost:8080/mcp
   Tools:     2 (from 1 API)

✓ Gateway ready
```

### 4. Connect Claude Desktop

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

Restart Claude. You now have MCP tools for every endpoint you configured. **Done.**

---

## Real-World Examples

<details>
<summary><strong>🏦 Internal APIs → AI Tools</strong></summary>

Expose your company's internal REST APIs to Claude without writing a single MCP server.

```yaml
apis:
  - name: "hr-system"
    base_url: "https://hr.internal.company.com/api"
    auth:
      type: bearer
      token: "${HR_API_TOKEN}"
    endpoints:
      - path: "/employees/{id}"
        method: GET
        tool_name: "get_employee"
        description: "Look up an employee by ID"
        parameters:
          - { name: id, in: path, required: true, type: string }

      - path: "/time-off/requests"
        method: POST
        tool_name: "submit_time_off"
        description: "Submit a time-off request"
        parameters:
          - { name: employee_id, in: body, required: true, type: string }
          - { name: start_date, in: body, required: true, type: string }
          - { name: end_date, in: body, required: true, type: string }
          - { name: reason, in: body, required: false, type: string }
```

Ask Claude: *"Submit a time-off request for employee E123 from Dec 24 to Jan 2"*

</details>

<details>
<summary><strong>🤖 Multi-Server Dev Workflow</strong></summary>

Aggregate GitHub, Jira, Slack, and your CI system into one AI-accessible gateway.

```yaml
mcp_servers:
  - name: github
    url: "https://api.githubcopilot.com/mcp/"
    auth: { type: bearer, token: "${GITHUB_TOKEN}" }
    namespace: gh

  - name: jira
    command: npx
    args: ["-y", "@modelcontextprotocol/server-jira"]
    env: { JIRA_TOKEN: "${JIRA_TOKEN}", JIRA_HOST: "company.atlassian.net" }
    namespace: jira

  - name: slack
    command: npx
    args: ["-y", "@slack/mcp-server"]
    namespace: slack

workflows:
  - name: "ship-feature"
    description: "Merge PR, close Jira ticket, and announce in Slack"
    steps:
      - id: merge
        tool: gh.merge_pull_request
        input: { pr_number: "{{input.pr_number}}", merge_method: squash }

      - id: close_ticket
        tool: jira.transition_issue
        input: { issue_key: "{{input.jira_key}}", status: Done }

      - id: announce
        tool: slack.post_message
        input:
          channel: "#releases"
          message: "🚀 Shipped: {{input.feature_name}} — PR #{{input.pr_number}} merged, {{input.jira_key}} closed"
```

Tell Claude: *"Ship feature login-redesign: PR #247, ticket FEAT-891"*

</details>

<details>
<summary><strong>📊 Data Pipeline Orchestration</strong></summary>

Chain API calls to build data enrichment pipelines your AI can trigger on demand.

```yaml
workflows:
  - name: "enrich-lead"
    description: "Enrich a sales lead with company and contact data"
    steps:
      - id: company_data
        tool: clearbit.get_company
        input: { domain: "{{input.domain}}" }

      - id: contact_data
        tool: hunter.find_email
        input:
          domain: "{{input.domain}}"
          first_name: "{{input.first_name}}"
          last_name: "{{input.last_name}}"

      - id: save_to_crm
        tool: hubspot.create_contact
        input:
          email: "{{contact_data.output.email}}"
          company: "{{company_data.output.name}}"
          employees: "{{company_data.output.metrics.employees}}"
```

</details>

---

## Configuration Reference

### Full Config Structure

```yaml
server:
  port: 8080                    # Gateway port (default: 8080)
  host: "0.0.0.0"              # Bind host
  name: "My Torii Gateway"     # Display name

apis:                           # REST APIs to convert
  - name: string                # Unique identifier
    base_url: string            # Base URL (no trailing slash)
    auth:
      type: bearer|api_key|basic|none
      token: string             # Bearer token (supports ${ENV_VAR})
      header: string            # Header name for api_key auth
      value: string             # Header value
    headers:                    # Static headers added to all requests
      X-Custom: value
    endpoints:
      - path: string            # Supports {path_params}
        method: GET|POST|PUT|PATCH|DELETE
        tool_name: string       # Lowercase snake_case MCP tool name
        description: string     # Shown to the AI — make it clear!
        parameters:
          - name: string
            in: path|query|body
            required: bool
            type: string|integer|number|boolean|object|array
            description: string
            default: any

mcp_servers:                    # Upstream MCP servers to aggregate
  - name: string
    url: string                 # HTTP/SSE server URL
    command: string             # Stdio server command (e.g. npx)
    args: [string]
    env: { KEY: VALUE }
    auth:
      type: bearer|api_key|none
      token: string
    namespace: string           # Tool prefix (e.g. "gh" → "gh.list_repos")

workflows:                      # Multi-step tool chains
  - name: string
    description: string
    steps:
      - id: string              # Referenced as {{id.output}} in later steps
        tool: string            # Any registered tool name
        input:
          key: "{{step_id.output}}" | "{{input.field}}" | literal
```

### Auth Types

| Type | Config | Header sent |
|---|---|---|
| `bearer` | `token: "${TOKEN}"` | `Authorization: Bearer <token>` |
| `api_key` | `header: X-API-Key`, `value: "${KEY}"` | `X-API-Key: <key>` |
| `basic` | `header: username`, `value: "${PASSWORD}"` | `Authorization: Basic <b64>` |
| `none` | — | — |

### Environment Variables

All string values in config support `${VAR_NAME}` expansion. Use `.env` files with [python-dotenv](https://github.com/theskumar/python-dotenv) or export directly:

```bash
export GITHUB_TOKEN=ghp_...
export STRIPE_KEY=sk_live_...
torii serve
```

---

## CLI Reference

```bash
torii serve                          # Start the gateway
torii serve --config custom.yaml     # Custom config path
torii serve --port 9090              # Override port
torii serve --verbose                # Debug logging

torii validate                       # Check config is valid
torii tools list                     # Preview all tools that will be exposed

torii version                        # Show version
```

**`torii tools list` output:**

```
┌──────────────────────────┬────────────────┬────────────────────────────────┐
│ Tool Name                │ Source         │ Description                    │
├──────────────────────────┼────────────────┼────────────────────────────────┤
│ get_customer             │ api stripe      │ Fetch a Stripe customer by ID  │
│ create_charge            │ api stripe      │ Create a new charge            │
│ gh.list_pull_requests    │ mcp github      │ List open pull requests        │
│ gh.create_issue          │ mcp github      │ Create a GitHub issue          │
│ slack.post_message       │ mcp slack       │ Post a message to a channel    │
│ workflow_ship_feature    │ workflow        │ Merge PR, close ticket, notify │
└──────────────────────────┴────────────────┴────────────────────────────────┘
```

---

## Connect Your AI Assistant

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "torii": { "url": "http://localhost:8080/mcp" }
  }
}
```

### Cursor

`.cursor/mcp.json`

```json
{
  "mcpServers": {
    "torii": { "url": "http://localhost:8080/mcp" }
  }
}
```

### VS Code Copilot

`.vscode/settings.json`

```json
{
  "mcp.servers": {
    "torii": { "type": "http", "url": "http://localhost:8080/mcp" }
  }
}
```

### Windsurf

```json
{
  "mcpServers": {
    "torii": { "serverUrl": "http://localhost:8080/mcp" }
  }
}
```

---

## Docker

```bash
# Run
docker run -p 8080:8080 \
  -v $(pwd)/torii.config.yaml:/app/torii.config.yaml \
  --env-file .env \
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
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AI Assistant / MCP Client                   │
│         Claude Desktop · Cursor · Windsurf · Copilot        │
└─────────────────────────────┬───────────────────────────────┘
                              │  MCP Protocol (JSON-RPC 2.0)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        ⛩️  TORII GATEWAY                     │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │   API Converter  │  │        MCP Aggregator            │ │
│  │                  │  │                                  │ │
│  │  REST endpoint   │  │  HTTP servers  +  stdio servers  │ │
│  │  → JSON Schema   │  │  → unified tool registry         │ │
│  │  → MCP Tool      │  │  → namespaced tool names         │ │
│  └────────┬─────────┘  └───────────────┬──────────────────┘ │
│           │                            │                     │
│  ┌────────▼────────────────────────────▼──────────────────┐ │
│  │                   Workflow Engine                       │ │
│  │   step1 → {{step1.output}} → step2 → {{step2.output}}  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Pydantic Config  +  Env Expansion         │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
   ┌───────────▼──────────┐  ┌────────────▼───────────────────┐
   │    Your REST APIs    │  │    Upstream MCP Servers        │
   │                      │  │                                │
   │  Stripe · Twilio     │  │  GitHub · Slack · Jira        │
   │  Internal APIs       │  │  Filesystem · Custom servers  │
   └──────────────────────┘  └────────────────────────────────┘
```

**Key design principles:**
- **Zero runtime dependencies on your APIs** — Torii proxies; it doesn't embed
- **Auth never touches the AI** — credentials stay in env vars, never in prompts
- **Additive, not invasive** — your APIs and MCP servers are unchanged
- **Async throughout** — built on `asyncio` + `httpx` for high concurrency

---

## Roadmap

**v0.1 — Foundation** ✅
- Dynamic API → MCP conversion
- HTTP + stdio MCP server aggregation
- Workflow engine with template variables
- Bearer / API key / basic auth
- Rich CLI with `serve`, `validate`, `tools list`

**v0.2 — Power Features** 🔜
- [ ] OpenAPI / Swagger spec auto-import (`torii import openapi spec.yaml`)
- [ ] GraphQL endpoint support
- [ ] Conditional workflow steps (`if: "{{step.output.status}} == error"`)
- [ ] Tool-level rate limiting and response caching
- [ ] Docker image published to GHCR

**v0.3 — Observability & Control** 📋
- [ ] Web UI — visual tool browser and workflow builder
- [ ] Structured audit logging (who called what, when, with what params)
- [ ] Prometheus metrics endpoint
- [ ] Per-tool access control (allow/deny lists)
- [ ] Hot config reload without restart

**v1.0 — Production Ready** 🎯
- [ ] TLS termination built in
- [ ] Multi-tenant support
- [ ] Torii Cloud — hosted gateway with zero infra

---

## Contributing

Torii is built in the open and contributions of all kinds are welcome.

```bash
git clone https://github.com/sarabala1979/Torii.git
cd Torii

# Set up dev environment
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/unit/ -v

# Lint
ruff check . && mypy torii/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines, commit conventions, and PR process.

**Good first issues:** look for the [`good first issue`](https://github.com/sarabala1979/Torii/labels/good%20first%20issue) label.

---

## Why "Torii"?

A **torii** (鳥居) is the iconic gate at the entrance to Japanese Shinto shrines. It marks the boundary between the ordinary world and something sacred — a threshold you pass through to reach a place of greater power.

Every API and every MCP server your AI needs to access passes through Torii. It's the threshold between your existing infrastructure and the AI-native future.

*One gate. Everything connected.*

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

⛩️ **[Getting Started](docs/getting-started.md)** · **[Examples](examples/)** · **[Issues](https://github.com/sarabala1979/Torii/issues)** · **[Discussions](https://github.com/sarabala1979/Torii/discussions)**

<br/>

**If Torii saves you time, consider giving it a ⭐**

*Configure once. Connect everything.*

</div>
