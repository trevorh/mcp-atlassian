package authz

default allow := false

# Health check — unauthenticated
allow if {
    input.request.path == "/healthz"
}

# MCP endpoint — require at least a Jira or Confluence PAT header
allow if {
    input.request.method == "POST"
    input.request.headers["x-atlassian-jira-personal-token"] != ""
}

allow if {
    input.request.method == "POST"
    input.request.headers["x-atlassian-confluence-personal-token"] != ""
}
