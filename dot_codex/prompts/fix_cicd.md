# **CI/CD Workflow Fixer**

**Description:**
Use GitHub CLI (`gh`) to inspect recent GitHub Actions workflows,
summarize their results, identify failures, diagnose the root cause, and
generate fixes. Output clear commands, patches, or pull-request steps
needed to resolve the issues.

------------------------------------------------------------------------

## **Instructions to the Model**

1.  **Check Recent Workflows**
    -   Use GitHub CLI commands such as:

        ``` bash
        gh run list --limit 20
        gh run view <run-id> --log
        ```

    -   Retrieve status, conclusion, and relevant metadata for each
        recent workflow run.
2.  **Identify Failed Workflows**
    -   For each run with a non-success conclusion, gather:
        -   The failing job(s)
        -   Failing steps
        -   Error logs
        -   Workflow file path (`.github/workflows/*.yml`)
        -   Commit SHA associated with the run
3.  **Diagnose the Failure**
    -   Explain *why* the workflow failed.
    -   Distinguish between:
        -   Syntax errors\
        -   Environment issues\
        -   Missing secrets\
        -   Dependency failures\
        -   Flaky tests\
        -   Incorrect caching\
        -   Broken build steps
4.  **Propose a Fix** For each failure:
    -   Provide minimal, actionable patches (YAML or code).\
    -   Suggest GitHub CLI commands to apply or test the fix.\
    -   Use patches in unified diff format when editing workflow files.\
    -   Optionally provide the exact `gh` commands to create a new
        branch and PR, e.g.:

        ``` bash
        gh pr create --fill
        ```
5.  **Output Format**
    -   **Summary of workflow status**
    -   **List of failures**
    -   **Root-cause analysis**
    -   **Proposed patches**
    -   **Commands to apply the fix**
    -   Everything should be deterministic and reproducible using `gh`.

------------------------------------------------------------------------

## **Example Commands to Use**

``` bash
gh run list
gh run view <id> --log
gh run rerun <id>
gh workflow view <workflow-file> --yaml
```

------------------------------------------------------------------------

## **Goal**

Return a complete plan --- including actionable CLI commands and patches
--- to fix all failing workflows so the CI/CD pipeline becomes fully
green.

