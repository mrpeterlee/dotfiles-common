---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(find:*)
argument-hint: [scope: all | specific-topic]
description: Update documentation in docs/ folder for future Claude sessions
---

## Context

Current documentation files:
!`find docs/ -name "*.md" 2>/dev/null | head -20`

Current project structure:
!`ls -la`

## Task

Update the documentation in the `docs/` folder to help future Claude sessions understand this codebase. Focus on: $ARGUMENTS

## Documentation Standards

When updating docs, ensure each document:

1. **Has a clear purpose** - State what the doc covers in the first paragraph
2. **Is scannable** - Use headers, bullet points, and code blocks
3. **Stays current** - Remove outdated information, add new features
4. **Links related docs** - Cross-reference other relevant documentation

## Required Documentation Structure

For each major area, ensure docs cover:

- **Overview** - What it is and why it exists
- **Architecture** - How components connect and interact
- **Key Files** - Important files and their purposes
- **Common Patterns** - Recurring patterns and conventions used
- **Getting Started** - How to work with this area

## Steps

1. Read existing docs in `docs/` folder
2. Analyze the current codebase structure
3. Identify gaps between code and documentation
4. Update or create documentation as needed
5. Ensure consistency across all docs
6. Summarize changes made

## Output

After updating, provide a summary of:
- Documents updated
- New documents created
- Key information added
- Any areas needing human review
