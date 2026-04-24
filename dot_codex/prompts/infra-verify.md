# Infrastructure Verification Prompt

When performing any cloud CLI operation (aws, aliyun, kubectl, terraform, argocd):

1. BEFORE each command: state the expected output
2. Use dry-run flags when available (terraform plan, kubectl diff, --dry-run)
3. AFTER each command: run a verification command to confirm the result
4. Log each step as [PASS] or [FAIL]
5. If any step fails: STOP. Do not proceed.

For multi-step operations: list ALL steps with expected outputs upfront, then execute one at a time.
