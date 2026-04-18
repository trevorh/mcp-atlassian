package authz

default allow := false

# Health check — unauthenticated
allow if {
    input.request.path == "/healthz"
}

# MCP endpoint — all POSTs allowed (auth via Atlassian PAT header, not SSO)
allow if {
    input.request.method == "POST"
}
