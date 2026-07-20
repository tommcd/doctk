/**
 * Python interpreter resolution and health checking.
 *
 * The extension previously spawned a bare `python3` from VS Code's inherited
 * PATH, which worked when VS Code was launched from an activated-venv
 * terminal and silently broke after a restart from the GUI. This module
 * resolves an interpreter deterministically and verifies doctk is importable
 * BEFORE any backend process is spawned, so failures surface as actionable
 * messages instead of a dead extension.
 *
 * Resolution order:
 *   1. `doctk.pythonPath` setting (explicit override)
 *   2. `doctk.lsp.pythonCommand` setting (legacy, deprecated)
 *   3. The ms-python extension's active interpreter for the workspace
 *   4. A `.venv` in the workspace root
 *   5. `python3` / `python` on PATH (last resort)
 */

import { execFile } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { getLogger } from './logger';

const logger = getLogger();

const HEALTH_CHECK_TIMEOUT_MS = 10000;

export interface ResolvedPython {
  /** Command or absolute path to the Python executable. */
  command: string;
  /** Human-readable description of how the interpreter was chosen. */
  source: string;
}

export interface HealthCheckResult {
  ok: boolean;
  /** doctk version reported by the interpreter (when ok). */
  version?: string;
  /** Actionable description of the failure (when not ok). */
  error?: string;
}

/**
 * Resolve the Python interpreter to use for the doctk backend.
 */
export async function resolvePythonInterpreter(resource?: vscode.Uri): Promise<ResolvedPython> {
  const config = vscode.workspace.getConfiguration('doctk');

  const explicit = config.get<string>('pythonPath', '').trim();
  if (explicit) {
    return { command: explicit, source: 'doctk.pythonPath setting' };
  }

  const legacy = config.get<string>('lsp.pythonCommand', '').trim();
  if (legacy && legacy !== 'python3') {
    return { command: legacy, source: 'doctk.lsp.pythonCommand setting (deprecated)' };
  }

  const fromMsPython = await getMsPythonInterpreter(resource);
  if (fromMsPython) {
    return { command: fromMsPython, source: 'ms-python extension active interpreter' };
  }

  const fromVenv = getWorkspaceVenvInterpreter();
  if (fromVenv) {
    return { command: fromVenv, source: 'workspace .venv' };
  }

  const fallback = process.platform === 'win32' ? 'python' : 'python3';
  return { command: fallback, source: 'PATH fallback' };
}

/**
 * Ask the ms-python extension for the active interpreter, if it is installed.
 */
async function getMsPythonInterpreter(resource?: vscode.Uri): Promise<string | undefined> {
  try {
    const msPython = vscode.extensions.getExtension('ms-python.python');
    if (!msPython) {
      return undefined;
    }
    if (!msPython.isActive) {
      await msPython.activate();
    }
    // Environments API (ms-python 2022.x+). Typed loosely on purpose: the
    // API surface varies across versions and must never break activation.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const environments = (msPython.exports as any)?.environments;
    const envPath = environments?.getActiveEnvironmentPath?.(resource);
    if (envPath?.path && typeof envPath.path === 'string') {
      return envPath.path;
    }
  } catch (error) {
    logger.warn('Could not query ms-python for an interpreter:', error);
  }
  return undefined;
}

/**
 * Look for a .venv in the first workspace folder.
 */
function getWorkspaceVenvInterpreter(): string | undefined {
  const root = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  if (!root) {
    return undefined;
  }
  const candidates =
    process.platform === 'win32'
      ? [path.join(root, '.venv', 'Scripts', 'python.exe')]
      : [path.join(root, '.venv', 'bin', 'python')];
  return candidates.find((candidate) => fs.existsSync(candidate));
}

/**
 * Verify that the interpreter exists and can import doctk.
 *
 * This runs before any backend process is spawned, so a broken environment
 * produces one clear message instead of a silently dead extension.
 */
export async function checkDoctkImportable(command: string): Promise<HealthCheckResult> {
  return new Promise((resolve) => {
    execFile(
      command,
      ['-c', 'import doctk; print(doctk.__version__)'],
      { timeout: HEALTH_CHECK_TIMEOUT_MS },
      (error, stdout, stderr) => {
        if (!error) {
          resolve({ ok: true, version: stdout.trim() });
          return;
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        if ((error as any).code === 'ENOENT') {
          resolve({
            ok: false,
            error:
              `Python interpreter not found: '${command}'. ` +
              `Set 'doctk.pythonPath' to a Python with doctk installed.`,
          });
          return;
        }
        const detail = stderr.trim().split('\n').pop() ?? '';
        resolve({
          ok: false,
          error:
            `doctk is not importable from '${command}'` +
            (detail ? ` (${detail})` : '') +
            `. Install it there (pip install doctk / uv pip install -e .) ` +
            `or point 'doctk.pythonPath' at the right interpreter.`,
        });
      }
    );
  });
}
