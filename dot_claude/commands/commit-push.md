---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git push:*), Bash(git log:*), Bash(git diff:*), Bash(git branch:*)
argument-hint: [optional: commit message override]
description: Commit all changes and push to origin main
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short`
- Staged changes: !`git diff --cached --stat`
- Unstaged changes: !`git diff --stat`
- Full diff: !`git diff HEAD`
- Recent commits (match this style): !`git log --oneline -5`

## Your Task

Commit all changes and push to origin main following this project's commit style.

$ARGUMENTS

## Commit Message Guidelines

This project uses **short, present-tense, lowercase summaries** without trailing punctuation.

**Format:** `<action> <what changed>`

**Good examples:**
- `added tmux session scripts`
- `updated nvim to latest`
- `fixed zsh prompt colors`
- `removed unused libs`

**Conventional Commits (alternative):**
- `feat: add dark mode toggle`
- `fix: resolve symlink conflict`
- `docs: update readme`
- `refactor: simplify install script`

## Steps

1. **Verify branch** - Confirm on `main` branch (warn if not)
2. **Check for secrets** - Scan diff for `.env`, tokens, keys, credentials - STOP if found
3. **Analyze changes** - Review the diff to understand what changed
4. **Generate message** - Create 3 candidate commit messages matching recent commit style
5. **Select best** - Pick the most descriptive message with brief reasoning
6. **Stage all changes** - Run `git add -A`
7. **Commit** - Execute commit with selected message (use HEREDOC for multiline)
8. **Push** - Run `git push origin main`
9. **Confirm** - Show final status

## Safety Rules

- NEVER commit files containing secrets, tokens, or credentials
- NEVER force push
- NEVER amend commits already pushed
- If on a feature branch, warn before pushing to main
- Include `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>` in commit footer

## Output

Provide the commit hash and confirmation message when complete.
