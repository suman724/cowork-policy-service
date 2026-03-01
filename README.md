# cowork-policy-service

Policy bundle generation service for the cowork platform. Reads tenant policy configurations from YAML files and generates `PolicyBundle` responses consumed by the Session Service during session handshake.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/policy-bundles?tenantId=...&userId=...&sessionId=...&capabilities=...` | Generate a policy bundle |
| GET | `/health` | Liveness check |
| GET | `/ready` | Readiness check |

## Development

```bash
# Install dependencies (requires cowork-platform sibling repo)
make install

# Run all checks (lint + format-check + typecheck + tests)
make check

# Run with uvicorn
uvicorn policy_service.main:app --reload

# Run tests with coverage
make coverage

# Build Docker image
make docker-build
```

## Configuration

Policy configurations live in `config/` as YAML files:

- `config/default_policy.yaml` — Default policy for all tenants
- `config/{tenant_id}_policy.yaml` — Tenant-specific overrides

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `dev` | Environment name |
| `LOG_LEVEL` | `info` | Logging level |
| `CONFIG_DIR` | `config` | Path to policy YAML files |
| `POLICY_EXPIRY_HOURS` | `24` | Hours until policy bundle expires |
| `SCHEMA_VERSION` | `1.0` | Policy bundle schema version |
