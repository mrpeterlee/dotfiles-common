#!/usr/bin/env node
/**
 * Python Quality Gate Hook (PostToolUse)
 *
 * Runs after .py file edits:
 *   1. ruff check --fix (lint + auto-fix)
 *   2. ruff format (formatting — supplements existing quality-gate.js)
 *   3. mypy --no-error-summary (type check, single file, non-blocking)
 *
 * Only fires on .py files. Skips if tools aren't installed.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

/**
 * Find the project root by walking up looking for pyproject.toml or setup.py.
 */
function findPythonRoot(startDir) {
  let dir = startDir;
  const fsRoot = path.parse(dir).root;
  let depth = 0;
  while (dir !== fsRoot && depth < 20) {
    if (
      fs.existsSync(path.join(dir, 'pyproject.toml')) ||
      fs.existsSync(path.join(dir, 'setup.py')) ||
      fs.existsSync(path.join(dir, 'Makefile'))
    ) {
      return dir;
    }
    dir = path.dirname(dir);
    depth++;
  }
  return startDir;
}

/**
 * Run a command, return { ok, stderr }.
 */
function exec(cmd, args, cwd) {
  const result = spawnSync(cmd, args, {
    cwd,
    encoding: 'utf8',
    env: process.env,
    timeout: 15000,
    stdio: ['pipe', 'pipe', 'pipe']
  });
  return {
    ok: result.status === 0,
    stderr: (result.stderr || '').trim(),
    stdout: (result.stdout || '').trim()
  };
}

/**
 * Check if a command exists.
 */
function hasCommand(cmd) {
  const which = process.platform === 'win32' ? 'where' : 'which';
  const result = spawnSync(which, [cmd], { encoding: 'utf8', timeout: 3000 });
  return result.status === 0;
}

function runPythonChecks(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return;

  const ext = path.extname(filePath).toLowerCase();
  if (ext !== '.py') return;

  const projectRoot = findPythonRoot(path.dirname(filePath));

  // 1. ruff check --fix (lint with auto-fix)
  if (hasCommand('ruff')) {
    const lintResult = exec('ruff', ['check', '--fix', filePath], projectRoot);
    if (!lintResult.ok && lintResult.stderr) {
      process.stderr.write(`[PythonQG] ruff check issues in ${path.basename(filePath)}:\n`);
      // Show first 10 lines of lint output
      const lines = (lintResult.stdout || lintResult.stderr).split('\n').slice(0, 10);
      lines.forEach(l => process.stderr.write(l + '\n'));
    }

    // 2. ruff format (already in quality-gate.js but harmless to re-run for consistency)
    exec('ruff', ['format', filePath], projectRoot);
  }

  // 3. mypy single-file check (non-blocking, informational)
  if (hasCommand('mypy')) {
    const mypyResult = exec('mypy', [
      '--no-error-summary',
      '--no-color-output',
      '--follow-imports=skip',
      filePath
    ], projectRoot);
    if (!mypyResult.ok && mypyResult.stdout) {
      const errors = mypyResult.stdout.split('\n').filter(l => l.includes('error:')).slice(0, 8);
      if (errors.length > 0) {
        process.stderr.write(`[PythonQG] mypy errors in ${path.basename(filePath)}:\n`);
        errors.forEach(l => process.stderr.write(l + '\n'));
      }
    }
  }
}

/**
 * Core logic — exported for run-with-flags.js.
 */
function run(rawInput) {
  try {
    const input = JSON.parse(rawInput);
    const filePath = String(input.tool_input?.file_path || '');
    runPythonChecks(path.resolve(filePath));
  } catch {
    // Ignore parse errors
  }
  return rawInput;
}

if (require.main === module) {
  const MAX_STDIN = 1024 * 1024;
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => {
    if (raw.length < MAX_STDIN) raw += chunk.substring(0, MAX_STDIN - raw.length);
  });
  process.stdin.on('end', () => {
    const result = run(raw);
    process.stdout.write(result);
  });
}

module.exports = { run };
