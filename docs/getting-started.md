# Getting Started with Torii ⛩️

This guide walks you through installing Torii, writing your first config, and connecting it to an AI assistant.

---

## 1. Installation

### From Source (Go)

```bash
git clone https://github.com/sarabala1979/Torii.git
cd Torii
go build -o bin/torii ./cmd/torii
./bin/torii --help
```

### Using `go install`

```bash
go install github.com/sarabala1979/Torii/cmd/torii@latest
torii --help
```

### Using Docker

```bash
docker pull ghcr.io/sarabala1979/torii:latest
docker run -p 8080:8080 ghcr.io/sarabala1979/torii:latest
```

---

## 2. Your First Config

Create a file called `torii.config.yaml`:

```yaml
server:
  port: 8080

apis:
  - name: "jsonplaceholder"
    base_url: "https://jsonplaceholder.typicode.com"
    endpoints:
      - path: "/posts/{id}"
        method: GET
        tool_name: "get_post"
        description: "Fetch a blog post by ID"
        parameters:
          - name: "id"
            in: "path"
            description: "Post ID (1-100)"
            required: true
            type: "string"

      - path: "/posts"
        method: GET
        tool_name: "list_posts"
        description: "List all blog posts"
```

Start the gateway:

```bash
torii serve --config torii.config.yaml
```

You should see:

```
⛩️  Torii gateway started on :8080
   Tools registered: get_post, list_posts
   MCP endpoint: http://localhost:8080/mcp
```

---

## 3. Connect to Claude Desktop

Open `~/Library/Application Support/Claude/claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "torii": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

Restart Claude Desktop. You should see `torii` appear in your connected tools.

Now you can ask Claude:
- *"Use the get_post tool to fetch post #5"*
- *"List all blog posts"*

---

## 4. Add a Real API

Let's add the OpenWeatherMap API. Get a free key at [openweathermap.org](https://openweathermap.org/api).

```yaml
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
        tool_name: "get_weather"
        description: "Get current weather for a city"
        parameters:
          - name: "q"
            in: "query"
            description: "City name"
            required: true
            type: "string"
```

Run with the env var:

```bash
WEATHER_API_KEY=your_key torii serve --config torii.config.yaml
```

---

## 5. Aggregate MCP Servers

Add other MCP servers to your config to aggregate them:

```yaml
mcp_servers:
  - name: "github"
    url: "https://api.githubcopilot.com/mcp/"
    auth:
      type: "bearer"
      token: "${GITHUB_TOKEN}"
    namespace: "gh"
```

All tools from the GitHub MCP server are now available through your single Torii endpoint, prefixed with `gh.` to avoid naming collisions.

---

## 6. Next Steps

- See the full [Configuration Reference](./configuration.md)
- Explore [example configs](../examples/)
- Learn about [Workflows](./workflows.md)
- [Contribute](../CONTRIBUTING.md) to Torii
