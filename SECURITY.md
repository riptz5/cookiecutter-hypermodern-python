# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by:

1. **DO NOT** open a public issue
2. Email the maintainers directly or use GitHub's private vulnerability reporting
3. Include detailed steps to reproduce the issue

## Security Best Practices for Agent Integrations

### API Keys and Secrets

**NEVER** commit secrets to the repository:

- `GOOGLE_API_KEY` - Gemini API access
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `LANGCHAIN_API_KEY` - LangSmith (optional)

Use these methods instead:

```bash
# Local development
cp .env.example .env
# Edit .env with your keys

# GitHub Actions
# Add secrets in Settings > Secrets and variables > Actions
```

### MCP Server Security

When deploying MCP servers:

1. Always use HTTPS in production
2. Implement authentication (API keys, OAuth)
3. Validate all tool inputs
4. Rate limit tool invocations
5. Sanitize tool outputs

### A2A Protocol Security

Agent-to-agent communication should:

1. Use HTTPS/TLS for all connections
2. Validate Agent Cards before trusting
3. Implement proper authorization (JWT, API keys)
4. Log all inter-agent communications
5. Never expose internal agent state

### Google Cloud Security

1. Use least-privilege IAM roles
2. Enable Cloud Audit Logs
3. Store secrets in Secret Manager
4. Use Workload Identity for authentication
5. Enable VPC Service Controls for sensitive workloads

## Protected Paths

The following paths require extra scrutiny:

- `.github/workflows/` - CI/CD configuration
- `tools/` - Release automation
- `**/agents/bridge.py` - Critical interop code
- `**/mcp/server.py` - External exposure

## Security Scanning

This project uses:

- Dependabot for dependency updates
- Bandit for Python security linting
- Safety for known vulnerabilities
- Pre-commit hooks for secret detection
