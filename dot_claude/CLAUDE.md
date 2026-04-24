# General AI Assistant Rules

Rules that apply across all repositories.

## Keyboard Layout

This user uses **Graphite** layout (not QWERTY). Navigation in vim/tmux/etc:
```
y = left    h = down    a = up    e = right
j = end-of-word    l = append    ' = yank
```

## Secrets Management

**NEVER hardcode sensitive data in any repository.** All secrets are managed through 1Password.

- Use `onepasswordRead` in chezmoi templates
- Use `op read` in shell scripts at runtime
- Use `.env` files that are `.gitignore`d for local dev
- Grep for sensitive patterns before committing:
  ```bash
  git diff --cached | grep -E "(password|secret|token|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"
  ```
