# **Improve Git Commit Message**

Task: For the most recent staged commit, modify the commit message to ensure it is descriptive in detail.


## Context and Example Behavior:

- Run git status, determine staged commit ahead of origin.
- Retrieve the most recent commit with git log -1 --stat.
- Assess commit diff (insertions, deletions, files changed).
- Attempt git commit --amend with detailed message.
- If permission denied (e.g., index.lock), investigate directory permissions and escalate if appropriate.
- Re-run amend step upon user approval.
- Confirm commit updated successfully.
- Summarize steps taken and advise user to run git push --force-with-lease after amending.


## Expected Output:

- A refined commit message including:
    - Clear title summarizing changes.
    - Bullet points describing test suites, config additions, refactors, relevant modules, and any batch runner updates.
- Notes on example configs, file movements, and added documentation.

## Usage:

- Codex should read current repo status.
- Amend the latest commit message with a detailed and structured explanation.
- Provide final instructions regarding pushing amended history.

