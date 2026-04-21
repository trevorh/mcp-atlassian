# Atlassian MCP Server (Disney)

MCP server for Jira and Confluence Data Center at Disney. Connects your AI assistant to Jira issues, Confluence pages, and project data over the [MCP protocol](https://modelcontextprotocol.io), deployed on Studioshare Launch.

Based on the open-source [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) project with additional analysis and structure tools.

## What Can It Do?

Ask your AI assistant to:

- **"Find my open Jira issues"** — search with JQL
- **"Summarize the PROJ-123 epic"** — children grouped by status, assignee, completion %
- **"Show cross-project dependencies for MYPROJ"** — find every link to other projects
- **"Search Confluence for onboarding docs"** — full-text search across spaces
- **"Create a bug ticket for the login issue"** — create, update, transition issues
- **"Trace the link graph from PROJ-456"** — BFS traversal of issue relationships

## Tools

### Jira (21 toolsets, 61 tools)

| Toolset | Tools |
|---------|-------|
| **Issues** | Search (JQL), get, create, update, delete, batch create, changelogs |
| **Fields** | Search fields, get field options |
| **Comments** | Add, edit comments |
| **Transitions** | Get available transitions, transition issues |
| **Filters** | Get saved filter, search filters, list favourites |
| **Projects** | List projects, versions, components |
| **Agile** | Boards, sprints, sprint issues |
| **Links** | Issue links, epic links, remote links |
| **Worklog** | Time tracking and work logs |
| **Attachments** | Download attachments and images |
| **Users** | User profile lookup |
| **Watchers** | Add/remove watchers |
| **Service Desk** | JSM queues and service desks |
| **Forms** | ProForma form operations |
| **Metrics** | Issue dates, SLA metrics |
| **Development** | Linked branches, PRs, commits |
| **Structures** | Almworks Structure boards — hierarchy and resolved issues |
| **Set Analysis** | Compare two JQL result sets — added, removed, changed fields |
| **Epic Analysis** | Epic summary with children grouped by status/assignee/type |
| **Project Analysis** | Epic hierarchy across projects, cross-project dependency map |
| **Link Analysis** | Link graph traversal (BFS), hierarchical issue tree |

### Confluence (6 toolsets, 24 tools)

| Toolset | Tools |
|---------|-------|
| **Pages** | Search (CQL), get, create, update, delete, children, history, diff |
| **Comments** | Add comments, reply to comments |
| **Labels** | Add/get labels |
| **Users** | User search |
| **Analytics** | Page view counts |
| **Attachments** | Upload, download, manage attachments |

All 27 toolsets (85 tools) are enabled on this deployment.

## Prerequisites

You need a **Jira Data Center Personal Access Token (PAT)**. Create one at:

https://jira.disney.com/secure/ViewProfile.jspa

Go to **Personal Access Tokens** and create a new token.

For Confluence access, also create a PAT at:

https://confluence.disney.com/plugins/personalaccesstokens/usertokens.action

## Client Setup

The server is deployed at:

```
https://atlassian-mcp.internal.launch.studioshare.wds.io/mcp
```

Set your PAT as an environment variable in your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export JIRA_PERSONAL_TOKEN="your-jira-pat-here"
export CONFLUENCE_PERSONAL_TOKEN="your-confluence-pat-here"  # optional
```

Then configure your AI tool:

### Claude Code

Add to `~/.claude/settings.json` or your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "type": "http",
      "url": "https://atlassian-mcp.internal.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Jira-Url": "https://jira.disney.com",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Url": "https://confluence.disney.com"
      }
    }
  }
}
```

### Claude Desktop

Go to **Settings > Developer > Edit Config** and add the same `mcpServers` block as above.

### Cursor

Add to `.cursor/mcp.json` in your project root (or global settings):

```json
{
  "mcpServers": {
    "atlassian": {
      "url": "https://atlassian-mcp.internal.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Jira-Url": "https://jira.disney.com",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Url": "https://confluence.disney.com"
      }
    }
  }
}
```

### Amazon Q Developer

Add to `~/.aws/amazonq/mcp.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "url": "https://atlassian-mcp.internal.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Jira-Url": "https://jira.disney.com",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Url": "https://confluence.disney.com"
      }
    }
  }
}
```

### Kiro

Add to `~/.kiro/mcp.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "url": "https://atlassian-mcp.internal.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Jira-Url": "https://jira.disney.com",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Url": "https://confluence.disney.com"
      }
    }
  }
}
```

### OpenAI Codex

```json
{
  "mcp_servers": {
    "atlassian": {
      "type": "url",
      "url": "https://atlassian-mcp.internal.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Jira-Url": "https://jira.disney.com",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Url": "https://confluence.disney.com"
      }
    }
  }
}
```

### Any MCP client (curl)

```bash
curl -X POST https://atlassian-mcp.internal.launch.studioshare.wds.io/mcp \
  -H "X-Atlassian-Jira-Personal-Token: $JIRA_PERSONAL_TOKEN" \
  -H "X-Atlassian-Jira-Url: https://jira.disney.com" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'
```

## Configuration

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-Atlassian-Jira-Personal-Token` | Yes (for Jira) | Your Jira DC Personal Access Token |
| `X-Atlassian-Jira-Url` | Optional | Defaults to `jira.disney.com` (server-side) |
| `X-Atlassian-Confluence-Personal-Token` | For Confluence | Your Confluence DC Personal Access Token |
| `X-Atlassian-Confluence-Url` | Optional | Defaults to `confluence.disney.com` (server-side) |

### Toolsets

This deployment has `TOOLSETS=all` — all 27 toolsets (85 tools) are active. The upstream project defaults to 6 core toolsets; we enable everything so all Jira and Confluence capabilities are available.

## Auth

Every request must include a valid Jira PAT via the `X-Atlassian-Jira-Personal-Token` header. The server passes it through to Jira/Confluence — no tokens are stored at rest.

The standard `Authorization` header does not work on Launch (the sidecar intercepts it), which is why this server uses custom `X-Atlassian-*` headers instead.

## Architecture

```
Client --> Launch NLB --> Ingress --> Sidecar (firewall, OPA) --> mcp-atlassian --> Jira/Confluence DC
```

- **Transport**: Streamable HTTP (stateless) at `/mcp`
- **Scaling**: Horizontally scalable — no session state
- **Health**: `/healthz` returns `{"status":"ok"}`

## Upstream

This deployment is based on [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian). The `disney` branch carries deployment config and additional tools; `main` tracks upstream.

See [docs/STUDIOSHARE.md](docs/STUDIOSHARE.md) for deployment setup and sync workflow.

## License

MIT - See [LICENSE](LICENSE).
