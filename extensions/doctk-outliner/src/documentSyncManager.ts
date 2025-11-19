/**
 * Document Synchronization Manager
 *
 * Manages bidirectional synchronization between the tree view and editor,
 * with error handling and recovery mechanisms.
 *
 * NOTE: Debouncing is handled by the outline provider to avoid double
 * debouncing. This manager focuses on preventing circular updates and
 * error recovery.
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
  // Configuration constants
  private static readonly ERROR_WARNING_THRESHOLD = 3;
  private static readonly MAX_ERRORS = 10;
  private static readonly RECOVERY_DELAY_MS = 1000;
  private static readonly ERROR_TTL_MS = 60000; // 1 minute

  private isUpdating = false;
  private lastSyncVersion = 0;
  private syncErrors: SyncError[] = [];

  constructor(private outlineProvider: DocumentOutlineProvider) {}

  /**
   * Handle document changes from the editor.
   *
   * This is called when the user types in the editor. The outline provider
   * handles its own debouncing, so we just coordinate the update here.
   *
   * @param document - The changed text document
   */
  onDocumentChange(document: vscode.TextDocument): void {
    // Prevent circular updates (when tree operations modify the document)
    if (this.isUpdating) {
      return;
    }

    try {
      this.outlineProvider.updateFromDocument(document);
      this.lastSyncVersion++;
      this.clearOldErrors();
    } catch (error) {
      this.handleSyncError({
        message: `Failed to update tree from document: ${this.formatError(error)}`,
        timestamp: Date.now(),
        recoverable: true,
        source: 'editor',
      });
    }
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
        message: `Failed to apply tree operation: ${this.formatError(error)}`,
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
    if (this.syncErrors.length > DocumentSyncManager.MAX_ERRORS) {
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
    } else if (this.syncErrors.length >= DocumentSyncManager.ERROR_WARNING_THRESHOLD) {
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
    setTimeout(() => {
      // Check if we're currently updating to avoid circular updates
      if (this.isUpdating) {
        console.log(`[DocumentSyncManager] Skipping recovery attempt - update in progress`);
        return;
      }

      try {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'markdown') {
          this.outlineProvider.updateFromDocument(editor.document);
          console.log(`[DocumentSyncManager] Recovery attempt succeeded for ${error.source} error`);
        }
      } catch (recoveryError) {
        console.error('[DocumentSyncManager] Recovery attempt failed:', recoveryError);
      }
    }, DocumentSyncManager.RECOVERY_DELAY_MS);
  }

  /**
   * Clear old errors (older than ERROR_TTL_MS).
   */
  private clearOldErrors(): void {
    const cutoffTime = Date.now() - DocumentSyncManager.ERROR_TTL_MS;
    this.syncErrors = this.syncErrors.filter((err) => err.timestamp > cutoffTime);
  }

  /**
   * Format error for display.
   *
   * @param error - Unknown error object
   * @returns Formatted error message
   */
  private formatError(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }
    return String(error);
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
    this.syncErrors = [];
  }
}
