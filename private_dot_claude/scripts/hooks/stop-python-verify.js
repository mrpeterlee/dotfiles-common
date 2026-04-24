#!/usr/bin/env node
/**
 * Stop Hook: Python project verification gate
 *
 * When the current working directory is a Python project (has pyproject.toml),
 * runs verification before allowing Claude to finish:
 *
 *   1. If Makefile has lint/typecheck/test targets → `make lint typecheck test`
 *   2. Otherwise → ruff check + mypy + pytest
 *
 * Exit code 2 blocks Claude from completing (forces it to fix issues first).
 * Only runs if .py files were edited this session (checks the accumulator).
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');
const { spawnSync } = require('child_process');

/**
 * Check if the accumulator has any .py files edited this session.
 */
function hasPythonEdits() {
  const raw =
    process.env.CLAUDE_SESSION_ID ||
    crypto.createHash('sha1').update(process.cwd()).digest('hex').slice(0, 12);
  const sessionId = raw.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64);
  const accumFile = path.join(os.tmpdir(), `ecc-edited-${sessionId}.txt`);

  try {
    const content = fs.readFileSync(accumFile, 'utf8');
    return content.split('\n').some(l => l.trim().endsWith('.py'));
  } catch {
    // No accumulator or can't read — check git for modified .py files instead
    const result = spawnSync('git', ['diff', '--name-only', '--diff-filter=ACMR', 'HEAD'], {
      cwd: process.cwd(),
      encoding: 'utf8',
      timeout: 5000
    });
    if (result.status === 0 && result.stdout) {
      return result.stdout.split('\n').some(l => l.trim().endsWith('.py'));
    }
    return false;
  }
}

/**
 * Check if a Makefile target exists.
 */
function hasMakeTarget(target) {
  const makefile = path.join(process.cwd(), 'Makefile');
  if (!fs.existsSync(makefile)) return false;
  try {
    const content = fs.readFileSync(makefile, 'utf8');
    return new RegExp(`^${target}\\s*:`, 'm').test(content);
  } catch {
    return false;
  }
}

/**
 * Check if a command exists on PATH.
 */
function hasCommand(cmd) {
  const which = process.platform === 'win32' ? 'where' : 'which';
  const result = spawnSync(which, [cmd], { encoding: 'utf8', timeout: 3000 });
  return result.status === 0;
}

/**
 * Run a command, print output, return success boolean.
 */
function runCmd(cmd, args, label) {
  process.stderr.write(`[PythonVerify] Running: ${label}...\n`);
  const result = spawnSync(cmd, args, {
    cwd: process.cwd(),
    encoding: 'utf8',
    env: process.env,
    timeout: 120000,
    stdio: ['pipe', 'pipe', 'pipe']
  });

  if (result.status !== 0) {
    const output = ((result.stdout || '') + '\n' + (result.stderr || '')).trim();
    // Show last 30 lines of output
    const lines = output.split('\n').slice(-30);
    process.stderr.write(`[PythonVerify] FAILED: ${label}\n`);
    lines.forEach(l => process.stderr.write(l + '\n'));
    return false;
  }

  process.stderr.write(`[PythonVerify] PASSED: ${label}\n`);
  return true;
}

function main() {
  // Only run in Python projects
  const hasPyProject = fs.existsSync(path.join(process.cwd(), 'pyproject.toml'));
  const hasSetupPy = fs.existsSync(path.join(process.cwd(), 'setup.py'));
  if (!hasPyProject && !hasSetupPy) return true;

  // Only run if Python files were edited
  if (!hasPythonEdits()) {
    process.stderr.write('[PythonVerify] No .py files edited — skipping verification\n');
    return true;
  }

  process.stderr.write('[PythonVerify] Python files edited — running verification gate\n');

  // Strategy 1: Use Makefile targets if available
  const useMake = hasMakeTarget('lint') && hasMakeTarget('test');
  if (useMake) {
    const targets = [];
    if (hasMakeTarget('lint')) targets.push('lint');
    if (hasMakeTarget('typecheck')) targets.push('typecheck');
    if (hasMakeTarget('test')) targets.push('test');

    const ok = runCmd('make', targets, `make ${targets.join(' ')}`);
    return ok;
  }

  // Strategy 2: Run individual tools
  let allPassed = true;

  if (hasCommand('ruff')) {
    if (!runCmd('ruff', ['check', '.'], 'ruff check')) {
      allPassed = false;
    }
  }

  if (hasCommand('mypy')) {
    // Use mypy with project config (pyproject.toml or mypy.ini)
    if (!runCmd('mypy', ['.', '--no-error-summary'], 'mypy')) {
      allPassed = false;
    }
  }

  if (hasCommand('pytest')) {
    if (!runCmd('pytest', ['--tb=short', '-q'], 'pytest')) {
      allPassed = false;
    }
  }

  return allPassed;
}

/**
 * Core logic — exported for run-with-flags.js.
 */
function run(rawInput) {
  try {
    const passed = main();
    if (!passed) {
      process.stderr.write('\n[PythonVerify] BLOCKED: Fix the above issues before completing.\n');
      process.exit(2);
    }
  } catch (err) {
    process.stderr.write(`[PythonVerify] Error: ${err.message}\n`);
    // Don't block on hook errors — fail open
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
