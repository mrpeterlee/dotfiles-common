---
name: git-workflow
description: "Branch naming conventions, commit message format, and PR templates. Use when creating branches, committing, or opening PRs."
user-invocable: true
argument-hint: "<branch-type> <description>"
allowed-tools:
  - Bash
---

# Git Workflow

## Branch Naming

Format: `<prefix>/<short-description>`

Prefixes: `feature/`, `bug/`, `fix/`, `hotfix/`, `chore/`, `docs/`, `test/`, `refactor/`

Examples:
- `feature/add-k8s-deploy-skill`
- `fix/broken-symlink-detection`
- `chore/update-cli-help`

## Commit Messages

Format: `<type>: <description>`

Types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `ci`

Rules:
- Lowercase, imperative mood
- No period at the end
- Under 72 characters
- Body optional, separated by blank line

Examples:
- `feat: add k8s-ops skill for EKS deployments`
- `fix: correct symlink path for opencode agents`
- `docs: update CLI help with opencode instructions`

## PR Template

Every PR description must include:
1. Purpose and affected scope
2. Risk assessment and rollback plan
3. Verification commands/evidence

## Parallel Agent Branches

When working with tiered parallel agents, use:
`{tier}_{sequence}-{description}`

```
1_1-setup-database
1_2-setup-redis
2_1-create-service
```
