# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

`cowork-policy-service` generates policy bundles that define what a session is allowed to do. It is the authoritative source for capability rules, approval requirements, LLM guardrail configuration, and token budgets. Called only by the Session Service — never by desktop clients directly.

## Tech Stack

Python, FastAPI, Pydantic models from `cowork-platform`.

## API Endpoint (Internal Only)

```
GET /policy-bundles?tenantId=...&userId=...&sessionId=...&capabilities=...
```

Returns a policy bundle JSON document.

## Policy Bundle Structure

```json
{
  "policyBundleVersion": "2026-02-21.1",
  "schemaVersion": "1.0",
  "tenantId": "...", "userId": "...", "sessionId": "...",
  "expiresAt": "...",
  "capabilities": [
    { "name": "File.Read", "allowedPaths": [...], "requiresApproval": false },
    { "name": "Shell.Exec", "allowedCommands": [...], "requiresApproval": true, "approvalRuleId": "..." }
  ],
  "llmPolicy": { "allowedModels": [...], "maxInputTokens": 64000, "maxOutputTokens": 4000, "maxSessionTokens": 250000 },
  "approvalRules": [{ "approvalRuleId": "...", "title": "...", "description": "..." }]
}
```

## Data Store

- **Phase 1:** Static configuration files (JSON/YAML) loaded at startup. No database.
- **Phase 3:** DynamoDB table `{env}-policies`, PK=`tenantId`, SK=`policyVersion`, GSI `tenantId-active-index` for per-tenant policy authoring.

## Capability Scope Fields

| Field | Applies to |
|-------|-----------|
| `allowedPaths` / `blockedPaths` | File.Read, File.Write, File.Delete |
| `allowedCommands` / `blockedCommands` | Shell.Exec |
| `allowedDomains` | Network.Http |
| `maxFileSizeBytes` | File.Read, File.Write, Workspace.Upload |
| `maxOutputBytes` | Shell.Exec, tool outputs |
| `requiresApproval` / `approvalRuleId` | All capabilities |

## Client-Side Validation

After receiving the bundle, the Local Agent Host must verify: `expiresAt` is in the future, `sessionId` matches, `schemaVersion` is supported. Bundle is not refreshed mid-session in Phase 1 — policy revocation is Phase 3.

## Design Doc

Full specification: `cowork-infra/docs/services/policy-service.md`

---

## Engineering Standards

### Project Structure

```
cowork-policy-service/
  CLAUDE.md
  README.md
  Makefile
  Dockerfile
  pyproject.toml
  .python-version             # 3.12
  .env.example
  config/                     # Phase 1: static policy config files
    default_policy.yaml       # Default policy bundle template
    capabilities.yaml         # Capability definitions
  src/
    policy_service/
      __init__.py
      main.py                 # FastAPI app factory with lifespan
      config.py               # pydantic-settings: Settings class
      dependencies.py         # FastAPI Depends providers
      routes/
        __init__.py
        health.py             # GET /health, GET /ready
        policy_bundles.py     # GET /policy-bundles
      services/
        __init__.py
        policy_service.py     # Bundle generation logic
        capability_resolver.py # Resolve capabilities per tenant/user
      repositories/
        __init__.py
        base.py               # PolicyRepository Protocol
        config_file.py        # Phase 1: reads from config/ YAML files
        dynamo.py             # Phase 3: DynamoDB repository
        memory.py             # InMemoryPolicyRepository for tests
      models/
        __init__.py
        domain.py             # PolicyBundle, Capability, LLMPolicy models
      exceptions.py
  tests/
    unit/
    service/                  # Phase 3 only (DynamoDB Local)
    fixtures/
    conftest.py
```

### Python Tooling

Same as session-service: Python 3.12+, ruff, mypy --strict, pytest, 90% unit coverage.

### Phase 1 vs Phase 3

- **Phase 1**: Policy rules are static YAML files in `config/`. The `ConfigFilePolicyRepository` loads them at startup. No DynamoDB.
- **Phase 3**: Per-tenant policy authoring via DynamoDB. `DynamoPolicyRepository` replaces `ConfigFilePolicyRepository`. Service tests added.

### Makefile Targets

Same standard set as session-service: `help`, `install`, `lint`, `format`, `format-check`, `typecheck`, `test`, `test-unit`, `test-service`, `test-integration`, `coverage`, `docker-build`, `check`, `clean`.

### Error Handling

Same pattern as session-service. Service-specific exceptions:
```
ServiceError (base)
  ├── PolicyConfigError      → 500 (invalid config file)
  ├── TenantNotFoundError    → 404 (Phase 3, unknown tenant)
  └── ValidationError        → 400, code: INVALID_REQUEST
```

### FastAPI Patterns

Same as session-service: app factory, lifespan, Depends injection, request ID middleware, structured logging, health endpoints.

This is an internal-only service — called only by Session Service. No direct desktop client access.

### Testing

- **Unit tests**: InMemory repos, test bundle generation with various tenant/user/capability combinations.
- **Policy bundle validation tests**: Generate bundles, validate against the JSON Schema from `cowork-platform`.
- **Capability resolution tests**: Various capability requests × static config → verify granted/denied capabilities.
- **Config file tests**: Test loading/parsing of YAML config files, error handling for malformed config.

### Docker

Same multi-stage pattern as session-service. Non-root user, health check.
