# Studioshare Launch Deployment

> Disney deployment of [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) on Studioshare Launch.

## Reference URLs

| Resource | URL |
|----------|-----|
| Production URL | https://atlassian-mcp.launch.studioshare.wds.io |
| Launch Dashboard | https://developer.studioshare.wds.io/apps/atlassian-mcp-XXXX |
| Launch Docs | https://developer.studioshare.wds.io/docs |
| GitLab Repo | https://gitlab.disney.com/Trevor.Hart/atlassian-mcp |
| Webhook URL | https://api.studioshare.wds.io/launch/webhooks/gitlab |
| Upstream Repo | https://github.com/sooperset/mcp-atlassian |

> Replace `atlassian-mcp-XXXX` with the actual app slug after `launch create`.

## How It Works

```
Client --> Launch NLB --> Ingress --> Sidecar (firewall, OPA) --> mcp-atlassian --> Jira/Confluence DC
```

- **Transport**: Streamable HTTP (stateless) at `/mcp`
- **Auth**: Per-request Jira/Confluence Personal Access Token via custom headers
- **Scaling**: Horizontally scalable — no session state
- **Endpoints**: Jira DC at `jira.disney.com`, Confluence DC at `confluence.disney.com` (pre-configured as env vars)

Users only need to provide their PAT — the Jira/Confluence URLs are configured server-side.

## Client Setup

All clients connect to the same URL and pass the same headers. You need a Jira Data Center
Personal Access Token (PAT) — create one at https://jira.disney.com/secure/ViewProfile.jspa
under "Personal Access Tokens".

If you also need Confluence access, create a PAT at
https://confluence.disney.com/plugins/personalaccesstokens/usertokens.action.

### Claude Code

Add to `~/.claude/settings.json` or your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "type": "http",
      "url": "https://atlassian-mcp.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}"
      }
    }
  }
}
```

Set in your shell profile:

```bash
export JIRA_PERSONAL_TOKEN="your-jira-pat"
export CONFLUENCE_PERSONAL_TOKEN="your-confluence-pat"  # optional
```

### Claude Desktop

Go to Settings > Developer > Edit Config and add the same `mcpServers` block as above.

### Cursor

Add to `.cursor/mcp.json` in your project root (or global settings):

```json
{
  "mcpServers": {
    "atlassian": {
      "url": "https://atlassian-mcp.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}"
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
      "url": "https://atlassian-mcp.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}"
      }
    }
  }
}
```

Or via CLI:

```bash
q mcp add atlassian --url https://atlassian-mcp.launch.studioshare.wds.io/mcp
```

### Kiro

Add to `~/.kiro/mcp.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "url": "https://atlassian-mcp.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}"
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
      "url": "https://atlassian-mcp.launch.studioshare.wds.io/mcp",
      "headers": {
        "X-Atlassian-Jira-Personal-Token": "${JIRA_PERSONAL_TOKEN}",
        "X-Atlassian-Confluence-Personal-Token": "${CONFLUENCE_PERSONAL_TOKEN}"
      }
    }
  }
}
```

### Any MCP client (curl)

```bash
curl -X POST https://atlassian-mcp.launch.studioshare.wds.io/mcp \
  -H "X-Atlassian-Jira-Personal-Token: $JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'
```

## Jira Data Center vs Cloud

This deployment is configured for **Jira Data Center** at `jira.disney.com`.

- **DC auth**: Personal Access Token via `X-Atlassian-Jira-Personal-Token` header
- **Cloud auth**: Would use API tokens — when Disney migrates to Cloud later this year, the
  server config will be updated (likely switching `JIRA_URL` and the auth mechanism)

The `Authorization` header does **not** work on Launch (see Gotchas below), which is why the
server uses the custom `X-Atlassian-*` headers instead.

## Launch Deployment Steps

### Prerequisites

```bash
curl -sSL https://install.internal.studioshare.wds.io/cli | sh
launch login
launch me   # verify your Disney email
```

### 1. Create the Launch App

From the **parent directory** (not inside the repo):

```bash
cd ~/path/to/parent-dir
launch create atlassian-mcp
```

Interactive prompts:
1. "Connect a GitLab repo?" > **Create a new repo**
2. Complete GitLab OAuth in the browser
3. Search for your namespace (e.g., `Trevor.Hart`)
4. Select your namespace

### 2. Add GitLab Webhook

```bash
glab api "projects/Trevor.Hart%2Fatlassian-mcp/hooks" -X POST \
  -f url="https://api.studioshare.wds.io/launch/webhooks/gitlab" \
  -f push_events=true \
  -f enable_ssl_verification=true
```

### 3. Set Health Check Path

```bash
curl -X PUT \
  -H "Authorization: Bearer $STUDIOSHARE_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.studioshare.wds.io/launch/apps/<APP_SLUG>" \
  -d '{"healthCheck": "/healthz", "public": true}'
```

### 4. Configure Firewall (Dashboard)

In the Launch dashboard > Settings > Firewall:
- Add Disney corporate IP ranges (office + VPN CIDRs)
- SSO is **off** — auth is via per-user Atlassian PAT

### 5. Add Custom Domain Alias (Dashboard)

1. Go to app Settings > Domains
2. Click **+ Add domain**
3. Enter subdomain: `atlassian-mcp`
4. Select domain: `launch.studioshare.wds.io`
5. Click **Add**

### 6. Set Environment Variables

```bash
launch env set TRANSPORT=streamable-http
launch env set STATELESS=true
launch env set PORT=8080
launch env set JIRA_URL=https://jira.disney.com
launch env set CONFLUENCE_URL=https://confluence.disney.com
```

### 7. Deploy

Push the code to the GitLab repo and it auto-deploys:

```bash
git remote add disney git@gitlab.disney.com:Trevor.Hart/atlassian-mcp.git
git push disney main
```

## Environment Variables

Set via `launch env set`:

| Variable | Value | Purpose |
|----------|-------|---------|
| `TRANSPORT` | `streamable-http` | HTTP transport mode |
| `STATELESS` | `true` | No session state (horizontally scalable) |
| `PORT` | `8080` | Listen port |
| `JIRA_URL` | `https://jira.disney.com` | Jira Data Center base URL |
| `CONFLUENCE_URL` | `https://confluence.disney.com` | Confluence Data Center base URL |

## Gotchas

### `Authorization` header conflict

The Launch sidecar intercepts `Authorization` headers even when SSO is off, returning 403.
This server supports custom headers that bypass the conflict:

- `X-Atlassian-Jira-Personal-Token` — Jira PAT
- `X-Atlassian-Jira-Url` — (optional, server-side default is already set)
- `X-Atlassian-Confluence-Personal-Token` — Confluence PAT
- `X-Atlassian-Confluence-Url` — (optional, server-side default is already set)

### Health check endpoint

The server's health check is at `/healthz` (not `/health`). Set this in the Launch app config.

### Transport configuration

The server reads `TRANSPORT`, `STATELESS`, and `PORT` from environment variables — no
Dockerfile changes needed. The ENTRYPOINT is `mcp-atlassian` which picks up env vars
automatically.

### The `/mcp` path

The streamable-http endpoint is at `/mcp`. All client configs must use the full URL:
`https://atlassian-mcp.launch.studioshare.wds.io/mcp`

## Post-Deploy

```bash
launch logs -f              # stream logs
launch app inspect          # check app status
launch deploy list          # list deployments

# Test the endpoint
curl https://atlassian-mcp.launch.studioshare.wds.io/healthz
```

## Syncing with Upstream

This repo is a deployment copy of [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian).
To pull upstream changes:

```bash
# In the GitHub fork
git fetch upstream
git merge upstream/main

# Push to GitLab deployment repo
git push disney main
```

When upstream merges one of our feature PRs, the corresponding commit can be dropped
during the next sync (the change will already be in upstream's main).
