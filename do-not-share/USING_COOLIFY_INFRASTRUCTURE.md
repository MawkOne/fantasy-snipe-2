# Using the Coolify Infrastructure for External Projects

This guide explains how to leverage the existing VIBN Coolify infrastructure — Gitea, preview URLs, dev containers, and deployments — for projects that aren't running on `vibnai.com`.

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Coolify Host                     │
│  ┌──────────┐  ┌──────────────┐             │
│  │  Gitea    │  │   Traefik    │             │
│  │ (Git)     │  │  (Reverse    │             │
│  │           │  │   Proxy)     │             │
│  └────┬─────┘  └──────┬───────┘             │
│       │               │                      │
│  ┌────▼───────────────▼──────────────────┐   │
│  │         Docker Containers              │   │
│  │  ┌──────────┐ ┌──────────┐           │   │
│  │  │vibn-dev  │ │  App     │  ...       │   │
│  │  │(sandbox) │ │(prod)    │           │   │
│  │  └──────────┘ └──────────┘           │   │
│  └────────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Key components:**
- **Coolify** — Docker hosting platform (like Vercel/Heroku but self-hosted). Manages containers, deployments, env vars, and SSL.
- **Gitea** — Self-hosted Git repository (like GitHub/GitLab but self-hosted). Stores code and triggers deployments.
- **Traefik** — Reverse proxy + SSL termination. Routes `*.vibnai.com` to the correct container.
- **PostgreSQL** — Shared database for the VIBN platform.

---

## Prerequisites

1. **Access to the Coolify host** at `159.203.20.137` (SSH key required)
2. **A Coolify API token** with deployment permissions
3. **A Gitea bot account** or personal access token for git operations
4. **The SSH private key** for `root@159.203.20.137`

---

## Option 1: Full VIBN-Style Project (Dev Container + Preview + Deploy)

This replicates the full VIBN project workflow: code in a sandbox container, preview via Traefik, and production deploy.

### 1. Create a Gitea Repository

```bash
curl -X POST "https://git.vibnai.com/api/v1/user/repos" \
  -H "Authorization: token <GITEA_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "description": "My project",
    "private": true,
    "auto_init": true
  }'
```

The repo will be at `https://git.vibnai.com/<org>/my-project.git`.

### 2. Provision a Dev Container

Dev containers are Coolify services with the `vibn-dev:latest` image. They mount a workspace volume and run `sleep infinity` so you can exec in.

```bash
# Create the service via Coolify API
curl -X POST "https://coolify.vibnai.com/api/v1/services" \
  -H "Authorization: Bearer <COOLIFY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "vibn-dev-my-project",
    "docker_compose": "services:\n  vibn-dev:\n    image: vibn-dev:latest\n    pull_policy: never\n    restart: unless-stopped\n    command: [\"sleep\", \"infinity\"]\n    working_dir: /workspace\n    volumes:\n      - workspace_volume:/workspace\n    environment:\n      VIBN_PROJECT_SLUG: my-project\n    networks:\n      - coolify\n    labels:\n      - \"traefik.enable=true\"\n      - \"traefik.docker.network=coolify\"",
    "connect_to_docker_network": true
  }'
```

### 3. Clone Code into the Container

```bash
ssh -i <key> root@159.203.20.137 \
  "docker exec vibn-dev-<uuid> sh -c 'git clone https://git.vibnai.com/<org>/my-project.git /workspace'"
```

### 4. Set Up a Preview URL

The dev server runs inside the container and is exposed via Traefik labels:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=coolify"
  - "traefik.http.routers.my-project-preview-<token>.rule=Host(`preview-0-my-project-<token>.preview.vibnai.com`)"
  - "traefik.http.routers.my-project-preview-<token>.entrypoints=https"
  - "traefik.http.routers.my-project-preview-<token>.tls=true"
  - "traefik.http.routers.my-project-preview-<token>.tls.certresolver=letsencrypt-dns"
  - "traefik.http.services.my-project-preview-<token>.loadbalancer.server.port=3000"
```

The `<token>` is a unique hex identifier (e.g., first 8 chars of a UUID) that prevents domain collisions.

### 5. Set Up a Production App

Create a Coolify application that deploys from the Gitea repo:

```bash
curl -X POST "https://coolify.vibnai.com/api/v1/applications" \
  -H "Authorization: Bearer <COOLIFY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "git_repository": "https://git.vibnai.com/<org>/my-project.git",
    "build_pack": "nixpacks",
    "ports": "3000:3000",
    "fqdn": "my-project-<workspace>.vibnai.com",
    "install_command": "npm install",
    "build_command": "npm run build",
    "start_command": "npm start"
  }'
```

### 6. Trigger a Deploy

```bash
curl -X POST "https://coolify.vibnai.com/api/v1/deploy?type=application&uuid=<app-uuid>" \
  -H "Authorization: Bearer <COOLIFY_TOKEN>"
```

---

## Option 2: Use Just the Dev Container (No Production Deploy)

If you only need a sandboxed development environment with a preview URL:

```bash
# 1. Ensure the container exists
ssh -i <key> root@159.203.20.137 \
  "docker inspect vibn-dev-<uuid> >/dev/null 2>&1 || docker run -d --name vibn-dev-<uuid> -v workspace_volume:/workspace vibn-dev:latest sleep infinity"

# 2. Push your code
scp -i <key> -r ./my-project root@159.203.20.137:/workspace/

# 3. Start a dev server
ssh -i <key> root@159.203.20.137 \
  "docker exec vibn-dev-<uuid> sh -c 'cd /workspace && npm install && npm run dev -- --host 0.0.0.0 --port 3000'"
```

The preview will be at `http://159.203.20.137:3000` or via a Traefik route if labels are configured.

---

## Option 3: Use Just the Gitea Repository (No Containers)

Simplest option — use Gitea as your git backend with auto-deploy via Coolify webhooks:

```bash
git remote add coolify https://git.vibnai.com/<org>/my-project.git
git push coolify main
```

Then set up a Coolify application that watches the `main` branch and auto-deploys on push.

---

## Environment Variables Reference

| Variable | Purpose | Required For |
|---|---|---|
| `COOLIFY_URL` | Coolify API endpoint (`https://coolify.vibnai.com`) | All Coolify API calls |
| `COOLIFY_API_TOKEN` | Bearer token for Coolify API | All Coolify API calls |
| `COOLIFY_SSH_HOST` | Coolify host IP (`159.203.20.137`) | SSH exec into containers |
| `COOLIFY_SSH_PORT` | SSH port (`22`) | SSH exec into containers |
| `COOLIFY_SSH_PRIVATE_KEY_B64` | Base64-encoded SSH private key | SSH exec into containers |
| `COOLIFY_SSH_USER` | SSH user (`root`) | SSH exec into containers |
| `DATABASE_URL` | PostgreSQL connection string | Database access |
| `TELEMETRY_SERVICE_URL` | Telemetry ingest endpoint (`http://telemetry.vibnai.com`) | Telemetry logging |
| `VIBN_SECRETS_KEY` | HMAC key for OpenCode passwords | OpenCode server auth |
| `GITHUB_TOKEN` | GitHub personal access token | `github_search` / `github_file` tools |
| `OPENROUTER_API_KEY` | OpenRouter API key | LLM access |

---

## Key API Endpoints

| Endpoint | Purpose |
|---|---|
| `https://coolify.vibnai.com/api/v1/` | Coolify management API |
| `https://git.vibnai.com/api/v1/` | Gitea git hosting API |
| `https://vibnai.com/api/mcp` | VIBN MCP tool proxy (for AI agents) |
| `https://vibnai.com/api/internal/opencode-tools` | OpenCode read-only tool proxy |
| `https://api.vibnai.com` | VIBN API |
| `https://agents.vibnai.com` | VIBN AI agent runner |
| `http://telemetry.vibnai.com/ingest` | Telemetry ingestion |

---

## Example: Using the MCP Tools from an External AI

If you want an external AI (Zed, Claude Code, Cursor) to access the VIBN infrastructure, mint a workspace API key:

```bash
curl -X POST "https://vibnai.com/api/workspaces/<workspace-slug>/keys" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session-cookie>" \
  -d '{
    "name": "external-agent",
    "projectId": "<optional-project-id>",
    "scopes": ["workspace:*"]
  }'
```

Then the external AI can call MCP tools:

```bash
curl -X POST "https://vibnai.com/api/mcp" \
  -H "Authorization: Bearer vibn_sk_..." \
  -H "Content-Type: application/json" \
  -d '{"action": "tools.http_fetch", "params": {"url": "https://example.com"}}'
```

Available external-access tools:
- `tools.http_fetch` — Fetch any public URL
- `tools.github_search` — Search public GitHub repos
- `tools.github_file` — Read a file from a public GitHub repo

---

## Diagnostics

```bash
# Check Coolify service status
curl -H "Authorization: Bearer <TOKEN>" https://coolify.vibnai.com/api/v1/services/<uuid>

# Check Gitea repo health
curl -H "Authorization: token <GITEA_TOKEN>" https://git.vibnai.com/api/v1/repos/<org>/<repo>

# Execute a command in a dev container
ssh -i <key> root@159.203.20.137 \
  "docker exec <container-name> sh -c 'echo hello'"

# Check telemetry service health
curl http://telemetry.vibnai.com/health/ready
```

---

## Security Notes

- **API keys are returned only once** — store them immediately. Only the SHA-256 hash is persisted.
- **Gitea bot tokens** should be workspace-scoped, not global.
- **SSH keys** should be dedicated deploy keys, not personal keys.
- **Force-pushing** to `coolify_gitea` main can cause deploy disruptions — use feature branches for non-urgent changes.
- The `vibn-dev` image runs as `uid 1000` (vibn user) — ensure file permissions match.