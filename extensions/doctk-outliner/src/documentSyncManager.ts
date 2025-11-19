/**
 * Document Synchronization Manager
 *
 * Manages bidirectional synchronization between the tree view and editor,
 * with debouncing, error handling, and recovery mechanisms.
 */

import * as vscode from 'vscode';
import { DocumentOutlineProvider } from './outlineProvider';

export interface SyncError {
  message: string;
  timestamp: number;
  recoverable: boolean;
  source: 'editor' | 'tree' | 'external';
}

export class DocumentSyncManager {
  private debounceTimer: NodeJS.Timeout | null = null;
  private readonly debounceDelay: number;
  private isUpdating = false;
  private lastSyncVersion = 0;
  private syncErrors: SyncError[] = [];
  private readonly maxErrors = 10;

  constructor(
    private outlineProvider: DocumentOutlineProvider,
    debounceDelay = 300 // milliseconds
  ) {
    this.debounceDelay = debounceDelay;
  }

  /**
   * Handle document changes from the editor.
   *
   * This is called when the user types in the editor or when external
   * modifications occur. Updates are debounced to prevent excessive refreshes.
   *
   * @param document - The changed text document
   */
  onDocumentChange(document: vscode.TextDocument): void {
    // Prevent circular updates (when tree operations modify the document)
    if (this.isUpdating) {
      return;
    }

    // Debounce updates to prevent excessive refreshes during rapid typing
    this.debounceUpdate(() => {
      try {
        this.outlineProvider.updateFromDocument(document);
        this.lastSyncVersion++;
        this.clearOldErrors();
      } catch (error) {
        this.handleSyncError({
          message: `Failed to update tree from document: ${error}`,
          timestamp: Date.now(),
          recoverable: true,
          source: 'editor',
        });
      }
    });
  }

  /**
   * Handle tree view changes (from operations).
   *
   * This is called when the user performs an operation in the tree view
   * (promote, demote, move, etc.). Sets the updating flag to prevent
   * circular updates.
   *
   * @param callback - Async callback that performs the tree operation
   */
  async onTreeViewChange(callback: () => Promise<void>): Promise<void> {
    this.isUpdating = true;
    try {
      await callback();
      this.lastSyncVersion++;
      this.clearOldErrors();
    } catch (error) {
      this.handleSyncError({
        message: `Failed to apply tree operation: ${error}`,
        timestamp: Date.now(),
        recoverable: true,
        source: 'tree',
      });
      throw error; // Re-throw to allow caller to handle
    } finally {
      this.isUpdating = false;
    }
  }

  /**
   * Handle external file modifications.
   *
   * This is called when the file is modified outside of VS Code or by
   * another extension. Attempts to reconcile changes and update both views.
   *
   * @param document - The externally modified document
   */
  async onExternalChange(document: vscode.TextDocument): Promise<void> {
    try {
      // Clear any pending debounced updates
      if (this.debounceTimer) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = null;
      }

      // Immediately update the tree view
      this.outlineProvider.updateFromDocument(document);
      this.lastSyncVersion++;

      // Show notification to user
      vscode.window.showInformationMessage(
        'Document outline updated due to external changes'
      );
    } catch (error) {
      this.handleSyncError({
        message: `Failed to handle external change: ${error}`,
        timestamp: Date.now(),
        recoverable: false,
        source: 'external',
      });
    }
  }

  /**
   * Debounce updates to prevent excessive refreshes.
   *
   * @param callback - The callback to debounce
   */
  private debounceUpdate(callback: () => void): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(callback, this.debounceDelay);
  }

  /**
   * Handle synchronization errors.
   *
   * Records the error and attempts recovery based on error type.
   * Shows error messages to the user for non-recoverable errors.
   *
   * @param error - The synchronization error
   */
  private handleSyncError(error: SyncError): void {
    // Record error
    this.syncErrors.push(error);
    if (this.syncErrors.length > this.maxErrors) {
      this.syncErrors.shift(); // Remove oldest error
    }

    // Log to console for debugging
    console.error(`[DocumentSyncManager] ${error.message}`, {
      source: error.source,
      recoverable: error.recoverable,
      timestamp: new Date(error.timestamp).toISOString(),
    });

    // Show error message to user
    if (!error.recoverable) {
      vscode.window.showErrorMessage(
        `Document synchronization error: ${error.message}. ` +
          'Try closing and reopening the file.'
      );
    } else if (this.syncErrors.length >= 3) {
      // Show warning if multiple errors occur
      vscode.window.showWarningMessage(
        'Multiple synchronization errors detected. Document outline may be out of sync.'
      );
    }

    // Attempt recovery for recoverable errors
    if (error.recoverable) {
      this.attemptRecovery(error);
    }
  }

  /**
   * Attempt to recover from a synchronization error.
   *
   * @param error - The error to recover from
   */
  private attemptRecovery(error: SyncError): void {
    // For now, simple recovery: refresh the outline from the current document
    setTimeout(() => {
      try {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'markdown') {
          this.outlineProvider.updateFromDocument(editor.document);
          console.log(`[DocumentSyncManager] Recovery attempt succeeded for ${error.source} error`);
        }
      } catch (recoveryError) {
        console.error('[DocumentSyncManager] Recovery attempt failed:', recoveryError);
      }
    }, 1000); // Wait 1 second before attempting recovery
  }

  /**
   * Clear old errors (older than 1 minute).
   */
  private clearOldErrors(): void {
    const oneMinuteAgo = Date.now() - 60000;
    this.syncErrors = this.syncErrors.filter((err) => err.timestamp > oneMinuteAgo);
  }

  /**
   * Get recent synchronization errors.
   *
   * @returns Array of recent sync errors
   */
  getRecentErrors(): readonly SyncError[] {
    return this.syncErrors;
  }

  /**
   * Get the current synchronization version.
   *
   * @returns Current sync version number
   */
  getSyncVersion(): number {
    return this.lastSyncVersion;
  }

  /**
   * Check if currently updating.
   *
   * @returns True if an update is in progress
   */
  isCurrentlyUpdating(): boolean {
    return this.isUpdating;
  }

  /**
   * Cleanup resources.
   */
  dispose(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    this.syncErrors = [];
  }
}
