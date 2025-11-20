/**
 * Logging utility for the doctk extension.
 *
 * Provides structured logging with configurable verbosity levels using
 * VS Code's OutputChannel API. This is the recommended approach for VS Code
 * extensions as it provides a dedicated output panel and avoids polluting
 * the developer console.
 */

import * as vscode from 'vscode';

/**
 * Log levels in order of severity.
 */
export enum LogLevel {
  Debug = 0,
  Info = 1,
  Warn = 2,
  Error = 3,
  None = 4,
}

/**
 * Logger for the doctk extension.
 *
 * Uses VS Code's OutputChannel to provide structured logging with
 * configurable verbosity levels.
 */
export class Logger {
  private static instance: Logger;
  private outputChannel: vscode.OutputChannel;
  private logLevel: LogLevel;

  private constructor() {
    this.outputChannel = vscode.window.createOutputChannel('doctk Outliner');
    this.logLevel = this.getConfiguredLogLevel();
  }

  /**
   * Get the singleton logger instance.
   */
  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  /**
   * Get the configured log level from VS Code settings.
   */
  private getConfiguredLogLevel(): LogLevel {
    const config = vscode.workspace.getConfiguration('doctk.logging');
    const level = config.get<string>('level', 'info');

    switch (level.toLowerCase()) {
      case 'debug':
        return LogLevel.Debug;
      case 'info':
        return LogLevel.Info;
      case 'warn':
        return LogLevel.Warn;
      case 'error':
        return LogLevel.Error;
      case 'none':
        return LogLevel.None;
      default:
        return LogLevel.Info;
    }
  }

  /**
   * Update the log level (called when configuration changes).
   */
  updateLogLevel(): void {
    this.logLevel = this.getConfiguredLogLevel();
  }

  /**
   * Show the output channel.
   */
  show(): void {
    this.outputChannel.show();
  }

  /**
   * Format a log message with timestamp and level.
   */
  private formatMessage(level: string, message: string, ...args: any[]): string {
    const timestamp = new Date().toISOString();
    const formattedArgs = args.length > 0 ? ' ' + args.map((arg) => this.formatArg(arg)).join(' ') : '';
    return `[${timestamp}] [${level}] ${message}${formattedArgs}`;
  }

  /**
   * Format an argument for logging.
   */
  private formatArg(arg: any): string {
    if (typeof arg === 'string') {
      return arg;
    }
    if (arg instanceof Error) {
      return arg.stack || arg.message;
    }
    try {
      return JSON.stringify(arg, null, 2);
    } catch {
      return String(arg);
    }
  }

  /**
   * Log a message if the current log level permits it.
   */
  private log(level: LogLevel, levelName: string, message: string, ...args: any[]): void {
    if (level >= this.logLevel) {
      const formattedMessage = this.formatMessage(levelName, message, ...args);
      this.outputChannel.appendLine(formattedMessage);
    }
  }

  /**
   * Log a debug message.
   */
  debug(message: string, ...args: any[]): void {
    this.log(LogLevel.Debug, 'DEBUG', message, ...args);
  }

  /**
   * Log an info message.
   */
  info(message: string, ...args: any[]): void {
    this.log(LogLevel.Info, 'INFO', message, ...args);
  }

  /**
   * Log a warning message.
   */
  warn(message: string, ...args: any[]): void {
    this.log(LogLevel.Warn, 'WARN', message, ...args);
  }

  /**
   * Log an error message.
   */
  error(message: string, ...args: any[]): void {
    this.log(LogLevel.Error, 'ERROR', message, ...args);
  }

  /**
   * Dispose the logger.
   */
  dispose(): void {
    this.outputChannel.dispose();
  }
}

/**
 * Get the global logger instance.
 */
export function getLogger(): Logger {
  return Logger.getInstance();
}
