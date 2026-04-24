---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git push:*), Bash(git log:*), Bash(git diff:*), Bash(git branch:*), Bash(git checkout:*), Bash(gh pr create:*), Bash(gh pr view:*)
argument-hint: [branch-name or PR title]
description: Commit changes, push branch, and create a pull request
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short`
- Changes to commit: !`git diff HEAD --stat`
- Full diff: !`git diff HEAD`
- Recent commits: !`git log --oneline -5`
- Remote tracking: !`git remote -v | head -2`

## Your Task

Commit all changes, push to a feature branch, and create a pull request.

Branch name or PR context: $ARGUMENTS

## Commit Message Guidelines

This project uses **short, present-tense, lowercase summaries**.

**Format:** `<action> <what changed>`

**Examples:**
- `added tmux session scripts`
- `fixed zsh prompt colors`
- `feat: add new keybinding`

## PR Description Guidelines

Per CLAUDE.md, PRs should include:
- **Scope** - Modules touched (e.g., `nvim/`, `zsh/`, `tmux/`)
- **Stow targets tested** - Which `stow` commands were verified
- **Platforms** - macOS / Linux / WSL
- **Screenshots** - If terminal appearance changed (note this)
- **External downloads** - Any curl/git installs to review

## Steps

1. **Check for secrets** - Scan diff for `.env`, tokens, credentials - STOP if found
2. **Verify branch status**
   - If on `main`: create feature branch from `$ARGUMENTS` or generate name from changes
   - If on feature branch: use current branch
3. **Analyze changes** - Understand what was modified
4. **Generate commit message** - Match project style
5. **Stage and commit**
   - `git add -A`
   - Commit with message (include co-author footer)
6. **Push branch**
   - `git push -u origin <branch-name>`
7. **Create PR** using `gh pr create`:
   ```bash
   gh pr create --title "<title>" --body "$(cat <<'EOF'
   ## Summary
   - <bullet points of changes>

   ## Scope
   - Modules: <list>
   - Stow targets tested: <list or "N/A">

   ## Platforms Verified
   - [ ] Linux
   - [ ] macOS
   - [ ] WSL

   ## Test Plan
   - [ ] <verification step>

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```
8. **Return PR URL**

## Safety Rules

- NEVER commit secrets or credentials
- NEVER force push
- NEVER push directly to main from this command
- Create feature branches with pattern: `feat/<name>`, `fix/<name>`, `docs/<name>`

## Output

Provide:
- Commit hash
- Branch name
- PR URL (clickable)
