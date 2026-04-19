package authz

default allow := false

# Health check — unauthenticated
allow if {
    input.request.path == "/healthz"
}

# MCP endpoint — require at least one valid auth credential

# PAT auth: Jira personal token
allow if {
    input.request.method == "POST"
    input.request.headers["x-atlassian-jira-personal-token"] != ""
}

# PAT auth: Confluence personal token
allow if {
    input.request.method == "POST"
    input.request.headers["x-atlassian-confluence-personal-token"] != ""
}

# OAuth / Bearer token auth
allow if {
    input.request.method == "POST"
    startswith(input.request.headers.authorization, "Bearer ")
}
