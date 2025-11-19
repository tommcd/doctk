/**
 * Language Server Client for doctk DSL.
 *
 * This module manages the lifecycle of the doctk language server, including:
 * - Starting the server process
 * - Stopping the server on deactivation
 * - Automatically restarting on crash
 * - Configuring server options and capabilities
 */

import * as vscode from 'vscode';
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from 'vscode-languageclient/node';

export class DoctkLanguageClient {
  private client: LanguageClient | null = null;
  private restartAttempts = 0;
  private maxRestartAttempts = 3;
  private restartDelay = 2000; // 2 seconds

  constructor(_context: vscode.ExtensionContext) {
    // Context not currently used but kept for future extensibility
  }

  /**
   * Start the language server.
   *
   * Initializes the language server client and connects to the server process.
   * The server is started using 'uv run python -m doctk.lsp.server'.
   *
   * @returns Promise that resolves when the server is started
   */
  async start(): Promise<void> {
    const config = vscode.workspace.getConfiguration('doctk');
    const enabled = config.get('lsp.enabled', true);

    if (!enabled) {
      console.log('doctk language server is disabled');
      return;
    }

    // Get workspace root
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
      console.warn('No workspace folder found, language server not started');
      return;
    }

    // Configure server options to run the language server via uv
    const serverOptions: ServerOptions = {
      command: 'uv',
      args: ['run', 'python', '-m', 'doctk.lsp.server'],
      options: {
        cwd: workspaceRoot,
        env: process.env,
      },
      transport: TransportKind.stdio,
    };

    // Configure client options
    const clientOptions: LanguageClientOptions = {
      // Document selectors - activate for .tk files and doctk language blocks
      documentSelector: [
        { scheme: 'file', language: 'doctk' },
        { scheme: 'file', pattern: '**/*.tk' },
      ],

      // Synchronize configuration section
      synchronize: {
        configurationSection: 'doctk.lsp',
        fileEvents: vscode.workspace.createFileSystemWatcher('**/*.tk'),
      },

      // Output channel for debugging
      outputChannelName: 'doctk Language Server',

      // Trace level for debugging (from configuration)
      traceOutputChannel: vscode.window.createOutputChannel('doctk LSP Trace'),
    };

    // Create and start the language client
    this.client = new LanguageClient(
      'doctkLanguageServer',
      'doctk Language Server',
      serverOptions,
      clientOptions
    );

    // Handle server crashes with automatic restart
    this.client.onDidChangeState((event) => {
      console.log(`Language server state changed: ${event.oldState} -> ${event.newState}`);

      // If server crashed, attempt to restart
      if (event.newState === 3) {
        // State.Stopped
        this.handleServerCrash();
      }
    });

    try {
      await this.client.start();
      console.log('doctk language server started successfully');
      this.restartAttempts = 0; // Reset restart counter on successful start
    } catch (error) {
      console.error('Failed to start language server:', error);
      vscode.window.showErrorMessage(
        `Failed to start doctk language server: ${error instanceof Error ? error.message : String(error)}`
      );
      throw error;
    }
  }

  /**
   * Stop the language server.
   *
   * @returns Promise that resolves when the server is stopped
   */
  async stop(): Promise<void> {
    if (this.client) {
      try {
        await this.client.stop();
        console.log('doctk language server stopped');
        this.client = null;
      } catch (error) {
        console.error('Error stopping language server:', error);
      }
    }
  }

  /**
   * Handle server crash by attempting automatic restart.
   *
   * Implements exponential backoff with a maximum number of restart attempts.
   * After max attempts, shows an error message and gives up.
   */
  private async handleServerCrash(): Promise<void> {
    if (this.restartAttempts >= this.maxRestartAttempts) {
      vscode.window.showErrorMessage(
        `doctk language server has crashed ${this.maxRestartAttempts} times. ` +
          'Please check the output channel for errors and restart VS Code.'
      );
      return;
    }

    this.restartAttempts++;
    const delay = this.restartDelay * this.restartAttempts; // Exponential backoff

    console.log(
      `Language server crashed. Attempting restart ${this.restartAttempts}/${this.maxRestartAttempts} in ${delay}ms...`
    );

    vscode.window.showWarningMessage(
      `doctk language server crashed. Restarting in ${delay / 1000} seconds...`
    );

    // Wait before restarting
    await new Promise((resolve) => setTimeout(resolve, delay));

    try {
      await this.stop();
      await this.start();
      vscode.window.showInformationMessage('doctk language server restarted successfully');
    } catch (error) {
      console.error('Failed to restart language server:', error);
      vscode.window.showErrorMessage(
        `Failed to restart language server: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Check if the language server is running.
   *
   * @returns True if the server is running, false otherwise
   */
  isRunning(): boolean {
    return this.client !== null;
  }

  /**
   * Get the underlying language client instance.
   *
   * @returns The language client or null if not started
   */
  getClient(): LanguageClient | null {
    return this.client;
  }
}
