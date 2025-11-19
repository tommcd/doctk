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
  State,
  Trace,
  TransportKind,
} from 'vscode-languageclient/node';

export class DoctkLanguageClient {
  private client: LanguageClient | null = null;
  private restartAttempts = 0;
  private maxRestartAttempts = 3;
  private restartDelay = 2000; // 2 seconds
  private traceOutputChannel: vscode.OutputChannel;
  private isManualShutdown = false;
  private isRestarting = false;

  constructor(_context: vscode.ExtensionContext) {
    // Context not currently used but kept for future extensibility
    // Initialize trace output channel once (reused across restarts)
    this.traceOutputChannel = vscode.window.createOutputChannel('doctk LSP Trace');
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

    // Get trace level from configuration
    const traceLevel = config.get<string>('lsp.trace', 'off');

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

      // Reuse trace output channel (initialized in constructor)
      traceOutputChannel: this.traceOutputChannel,
    };

    // Create and start the language client
    this.client = new LanguageClient(
      'doctkLanguageServer',
      'doctk Language Server',
      serverOptions,
      clientOptions
    );

    // Set trace level from configuration
    // Must be done after client creation but before start
    await this.client.setTrace(this._mapTraceLevel(traceLevel));

    // Handle server crashes with automatic restart
    this.client.onDidChangeState((event) => {
      console.log(`Language server state changed: ${event.oldState} -> ${event.newState}`);

      // If server stopped unexpectedly (crashed), attempt to restart
      // Only trigger crash handler if:
      // 1. New state is Stopped (1)
      // 2. Not a manual shutdown (deactivation)
      // 3. Not already in the process of restarting
      if (event.newState === State.Stopped && !this.isManualShutdown && !this.isRestarting) {
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
        // Mark as manual shutdown to prevent crash handler from firing
        this.isManualShutdown = true;
        await this.client.stop();
        console.log('doctk language server stopped');
        this.client = null;
      } catch (error) {
        console.error('Error stopping language server:', error);
      } finally {
        // Reset flag after stop completes or fails
        this.isManualShutdown = false;
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
    // Prevent concurrent restart attempts
    if (this.isRestarting) {
      return;
    }

    if (this.restartAttempts >= this.maxRestartAttempts) {
      vscode.window.showErrorMessage(
        `doctk language server has crashed ${this.maxRestartAttempts} times. ` +
          'Please check the output channel for errors and restart VS Code.'
      );
      return;
    }

    this.isRestarting = true;
    this.restartAttempts++;

    // Exponential backoff: 2s, 4s, 8s
    const delay = this.restartDelay * Math.pow(2, this.restartAttempts - 1);

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
    } finally {
      this.isRestarting = false;
    }
  }

  /**
   * Check if the language server is running.
   *
   * @returns True if the server is running, false otherwise
   */
  isRunning(): boolean {
    return this.client !== null && this.client.state === State.Running;
  }

  /**
   * Get the underlying language client instance.
   *
   * @returns The language client or null if not started
   */
  getClient(): LanguageClient | null {
    return this.client;
  }

  /**
   * Map trace level string to Trace enum.
   *
   * @param traceLevel - Trace level string from configuration
   * @returns Trace enum value
   */
  private _mapTraceLevel(traceLevel: string): Trace {
    switch (traceLevel.toLowerCase()) {
      case 'off':
        return Trace.Off;
      case 'messages':
        return Trace.Messages;
      case 'verbose':
        return Trace.Verbose;
      default:
        console.warn(`Unknown trace level: ${traceLevel}, using 'off'`);
        return Trace.Off;
    }
  }
}
