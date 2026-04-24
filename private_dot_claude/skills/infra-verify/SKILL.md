---
name: infra-verify
description: "Plan verifiable outputs before any cloud CLI command, then verify after each step. Use for aws, aliyun, kubectl, terraform, argocd operations."
user-invocable: true
argument-hint: "<describe the infrastructure change>"
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
---

# Infrastructure Verification-First Workflow

## Hard Rule

**NEVER execute a cloud CLI command without first defining its expected output.**

## Process

For every infrastructure operation:

### 1. State Intent

Before any command, write:
- **Action:** What you are about to do (one sentence)
- **Command:** The exact CLI command
- **Expected output:** What success looks like (specific text, status codes, resource states)
- **Rollback:** How to undo this if it fails

### 2. Dry Run (when available)

Use dry-run flags when the CLI supports them:
- `terraform plan` before `terraform apply`
- `kubectl diff` before `kubectl apply`
- `aws ... --dry-run` where supported
- `aliyun ... --DryRun true` where supported

### 3. Execute

Run the command.

### 4. Verify

Run a verification command and compare actual output to expected output:
- `kubectl get <resource> -o json | jq '.status'`
- `aws <service> describe-<resource>`
- `aliyun <service> Describe<Resource>`
- `terraform show`

### 5. Record

After verification, log the result:

```
[PASS] <action> - <actual matches expected>
[FAIL] <action> - Expected: <x>, Got: <y>
```

If FAIL: stop, do not proceed to next step. Investigate.

## Multi-Step Operations

For operations with multiple steps:
1. List ALL steps upfront with expected outputs
2. Execute one step at a time
3. Verify each step before proceeding
4. If any step fails, stop and reassess

## Environment Detection

Detect which cloud you are operating in:

```bash
if command -v aws &>/dev/null && [[ "$(aws configure get region 2>/dev/null)" == "ap-southeast-1" ]]; then
  echo "ACAP: AWS ap-southeast-1"
elif command -v aliyun &>/dev/null; then
  echo "TapaiGroup: Aliyun"
fi
```
