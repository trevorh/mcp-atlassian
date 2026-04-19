# Studioshare Launch Deployment

> Disney deployment of [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) on Studioshare Launch.

## Reference URLs

| Resource | URL |
|----------|-----|
| Production URL | https://atlassian-disney-mcp.launch.studioshare.wds.io |
| Launch Dashboard | https://developer.studioshare.wds.io/apps/atlassian-mcp |
| Launch Docs | https://developer.studioshare.wds.io/docs |
| GitLab Repo | https://gitlab.disney.com/Trevor.Hart/atlassian-mcp |
| Webhook URL | https://api.studioshare.wds.io/launch/webhooks/gitlab |
| Upstream Repo | https://github.com/sooperset/mcp-atlassian |


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
      "url": "https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp",
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
      "url": "https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp",
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
      "url": "https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp",
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

Or via CLI:

```bash
q mcp add atlassian --url https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp
```

### Kiro

Add to `~/.kiro/mcp.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "url": "https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp",
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
      "url": "https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp",
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
curl -X POST https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp \
  -H "X-Atlassian-Jira-Personal-Token: $JIRA_PERSONAL_TOKEN" \
  -H "X-Atlassian-Jira-Url: https://jira.disney.com" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
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

This creates GitLab repo `gitlab.disney.com/Trevor.Hart/atlassian-mcp` with a scaffold commit.

### 2. Push the Code

The scaffold needs to be replaced with the actual codebase. Push the
`disney` branch (the deployment branch) and align `main` with upstream:

```bash
git remote add disney git@gitlab.disney.com:Trevor.Hart/atlassian-mcp.git

# Push the deployment branch
git push disney disney

# Align gitlab main with upstream main (unprotect, push, re-protect)
glab api "projects/Trevor.Hart%2Fatlassian-mcp/protected_branches/main" -X DELETE
git push --force disney main
glab api "projects/Trevor.Hart%2Fatlassian-mcp/protected_branches" -X POST \
  -f name=main -f push_access_level=40 -f merge_access_level=40
```

Then set the **production branch** to `disney` in the Launch app settings
(Dashboard > Settings > General > Production branch).

### 3. Add GitLab Webhook

```bash
glab api "projects/Trevor.Hart%2Fatlassian-mcp/hooks" -X POST \
  -f url="https://api.studioshare.wds.io/launch/webhooks/gitlab" \
  -f push_events=true \
  -f enable_ssl_verification=true
```

### 4. Link the Directory and Set Environment Variables

```bash
launch link atlassian-mcp
launch env set TRANSPORT streamable-http
launch env set STATELESS true
launch env set PORT 8080
launch env set JIRA_URL https://jira.disney.com
launch env set CONFLUENCE_URL https://confluence.disney.com
launch env set JIRA_PERSONAL_TOKEN dummy-placeholder-for-header-auth -s
launch env set CONFLUENCE_PERSONAL_TOKEN dummy-placeholder-for-header-auth -s
launch env set ATLASSIAN_OAUTH_ENABLE false
launch env set MCP_ALLOWED_URL_DOMAINS disney.com
```

**Note:** `launch env set` takes two args (`NAME VALUE`), not `NAME=VALUE`. The `-s` flag
marks a variable as sensitive (hidden in the dashboard UI).

**Critical env vars explained:**
- `JIRA_PERSONAL_TOKEN` / `CONFLUENCE_PERSONAL_TOKEN` — set to dummy placeholder values so
  the server config loads with `auth_type=pat`. The actual per-request PAT from client
  headers overrides these at runtime. Without these, the server either fails to start
  (missing auth) or falls through to OAuth and crashes.
- `ATLASSIAN_OAUTH_ENABLE=false` — must be false. Setting it to true makes the server config
  load as `auth_type=oauth`, causing "Failed to configure OAuth session" errors on tool calls
  even when PAT headers are present.
- `MCP_ALLOWED_URL_DOMAINS=disney.com` — allows `jira.disney.com` and `confluence.disney.com`
  through the SSRF validator. These hostnames resolve to private IPs (10.x.x.x) which the
  default SSRF check blocks.

### 5. Set Health Check Path and Public Access

```bash
curl -X PUT \
  -H "Authorization: Bearer $STUDIOSHARE_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.studioshare.wds.io/launch/apps/atlassian-mcp" \
  -d '{"healthCheck": "/healthz", "public": true}'
```

### 6. Add Custom Domain Alias (Dashboard)

1. Go to app Settings > Domains
2. Click **+ Add domain**
3. Enter subdomain: `atlassian-disney-mcp` (plain `atlassian-mcp` was taken)
4. Select domain: `launch.studioshare.wds.io`
5. Click **Add**

### 7. Trigger Deploy

Env vars are only picked up on new deploys. If the first build started before env
vars were set (it will run in `stdio` mode and fail health checks), push a new
commit to trigger a fresh build:

```bash
git commit --allow-empty -m "chore: redeploy with env vars"
git push disney disney
```

### 8. Configure Firewall (Dashboard)

In the Launch dashboard > Settings > Firewall:
- Add Disney corporate IP ranges (office + VPN CIDRs)
- SSO is **off** — auth is via per-user Atlassian PAT

### Verify

```bash
curl https://atlassian-disney-mcp.launch.studioshare.wds.io/healthz
# => {"status":"ok"}

curl -X POST https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp \
  -H "X-Atlassian-Jira-Personal-Token: $JIRA_PERSONAL_TOKEN" \
  -H "X-Atlassian-Jira-Url: https://jira.disney.com" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'
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
| `JIRA_PERSONAL_TOKEN` | `dummy-placeholder-for-header-auth` | Dummy PAT so config loads as `auth_type=pat` (sensitive) |
| `CONFLUENCE_PERSONAL_TOKEN` | `dummy-placeholder-for-header-auth` | Dummy PAT so config loads as `auth_type=pat` (sensitive) |
| `ATLASSIAN_OAUTH_ENABLE` | `false` | Must be false — true causes OAuth session errors |
| `MCP_ALLOWED_URL_DOMAINS` | `disney.com` | Bypass SSRF check for Disney internal hostnames (private IPs) |

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
`https://atlassian-disney-mcp.launch.studioshare.wds.io/mcp`

## Post-Deploy

```bash
launch logs -f              # stream logs
launch app inspect          # check app status
launch deploy list          # list deployments

# Test the endpoint
curl https://atlassian-disney-mcp.launch.studioshare.wds.io/healthz
```

## Branch Model

| Branch | Where | Purpose |
|--------|-------|---------|
| `main` | gitlab + github | Tracks upstream `sooperset/mcp-atlassian` main |
| `disney` | gitlab | Deployment branch — all Disney config + feature work |
| `feat/*` | github (origin) | Upstream PRs against `sooperset/mcp-atlassian` |

Launch production deploys from the **`disney`** branch. Gitlab `main`
stays aligned with upstream so it can serve as a clean merge base.

## Syncing with Upstream

This repo is a deployment copy of [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian).
To pull upstream changes:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push disney main          # keep gitlab main aligned

git checkout disney
git merge main                # bring upstream changes into deployment branch
git push disney disney        # triggers production deploy
```

When upstream merges one of our feature PRs, the corresponding commit can be dropped
during the next sync (the change will already be in upstream's main).
