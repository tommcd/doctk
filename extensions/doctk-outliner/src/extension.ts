/**
 * VS Code extension entry point for doctk outliner.
 */

import * as vscode from 'vscode';
import { DocumentOutlineProvider } from './outlineProvider';
import { PythonBridge } from './pythonBridge';
import { DocumentSyncManager } from './documentSyncManager';
import { DoctkLanguageClient } from './languageClient';
import { OutlineNode } from './types';
import { getLogger } from './logger';

let outlineProvider: DocumentOutlineProvider;
let pythonBridge: PythonBridge;
let syncManager: DocumentSyncManager;
let languageClient: DoctkLanguageClient;
let treeView: vscode.TreeView<any>;
const logger = getLogger();

/**
 * Activate the extension.
 *
 * @param context - Extension context
 */
export async function activate(context: vscode.ExtensionContext) {
  logger.info('doctk outliner extension is now active');

  // Initialize Language Server Client first
  languageClient = new DoctkLanguageClient(context);
  try {
    await languageClient.start();
    logger.info('doctk language server started successfully');
  } catch (error) {
    logger.error('Failed to start language server:', error);
    // Non-fatal - continue with extension activation
  }

  // Initialize Python bridge for outliner operations
  const config = vscode.workspace.getConfiguration('doctk');
  pythonBridge = new PythonBridge({
    pythonCommand: config.get('lsp.pythonCommand', 'python3'),
    cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
  });

  try {
    await pythonBridge.start();
    logger.info('Python bridge started successfully');
  } catch (error) {
    logger.error('Failed to start Python bridge:', error);
    vscode.window.showErrorMessage('Failed to start doctk backend. Some features may not work.');
  }

  // Initialize outline provider with Python bridge for centralized ID generation
  outlineProvider = new DocumentOutlineProvider(pythonBridge);

  // Initialize document synchronization manager
  // Note: Debouncing is handled by outline provider to avoid double debouncing
  syncManager = new DocumentSyncManager(outlineProvider);

  // Register tree data provider with drag-and-drop support
  logger.debug('Creating tree view with ID: doctkOutline');
  treeView = vscode.window.createTreeView('doctkOutline', {
    treeDataProvider: outlineProvider,
    showCollapseAll: true,
    canSelectMany: false,
    dragAndDropController: outlineProvider,
  });
  logger.debug('Tree view created successfully');

  // Register sync manager for disposal
  context.subscriptions.push({
    dispose: () => syncManager.dispose(),
  });

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.refresh', () => {
      const editor = vscode.window.activeTextEditor;
      if (editor && editor.document.languageId === 'markdown') {
        syncManager.onDocumentChange(editor.document);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.navigateToNode', (node: OutlineNode) => {
      const editor = vscode.window.activeTextEditor;
      if (editor && node.range) {
        editor.selection = new vscode.Selection(node.range.start, node.range.end);
        editor.revealRange(node.range, vscode.TextEditorRevealType.InCenter);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.promote', async (node: OutlineNode) => {
      try {
        await executeOperation('promote', node);
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to promote section: ${error instanceof Error ? error.message : String(error)}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.demote', async (node: OutlineNode) => {
      try {
        await executeOperation('demote', node);
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to demote section: ${error instanceof Error ? error.message : String(error)}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.moveUp', async (node: OutlineNode) => {
      try {
        await executeOperation('move_up', node);
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to move section up: ${error instanceof Error ? error.message : String(error)}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.moveDown', async (node: OutlineNode) => {
      try {
        await executeOperation('move_down', node);
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to move section down: ${error instanceof Error ? error.message : String(error)}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.delete', async (node: OutlineNode) => {
      try {
        await executeOperation('delete', node);
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to delete section: ${error instanceof Error ? error.message : String(error)}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.rename', async (node: OutlineNode) => {
      try {
        // Show input box with current heading text
        const newText = await vscode.window.showInputBox({
          prompt: 'Enter new heading text',
          value: node.label,
          validateInput: (value) => {
            if (!value || value.trim().length === 0) {
              return 'Heading text cannot be empty';
            }
            return null;
          }
        });

        // User cancelled (pressed Escape)
        if (newText === undefined) {
          return;
        }

        // Trim text once and reuse (avoid multiple trim() calls and inconsistent user feedback)
        const trimmedText = newText.trim();

        // Update the heading in the document
        const editor = vscode.window.activeTextEditor;
        if (!editor || !node.range) {
          vscode.window.showErrorMessage('No active editor or invalid node range');
          return;
        }

        await syncManager.onTreeViewChange(async () => {
          const edit = new vscode.WorkspaceEdit();

          // Extract the heading line and replace only the text part (preserve the # symbols)
          const headingLine = editor.document.lineAt(node.range.start.line);
          const headingPrefix = '#'.repeat(node.level) + ' ';
          const newHeadingLine = headingPrefix + trimmedText;

          // Replace the entire line
          const lineRange = new vscode.Range(
            headingLine.range.start,
            headingLine.range.end
          );
          edit.replace(editor.document.uri, lineRange, newHeadingLine);

          const success = await vscode.workspace.applyEdit(edit);
          if (!success) {
            throw new Error('Failed to apply edit');
          }

          // Rebuild tree with updated document content (not just refresh UI)
          // This ensures the tree displays the new heading text immediately
          outlineProvider.updateFromDocument(editor.document);
        });

        vscode.window.showInformationMessage(`Renamed heading to: ${trimmedText}`);
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to rename section: ${error instanceof Error ? error.message : String(error)}`);
      }
    })
  );

  // Listen for active editor changes
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      logger.debug('Active editor changed');
      if (editor) {
        logger.debug(`New editor: ${editor.document.uri.fsPath}, language: ${editor.document.languageId}`);
        if (editor.document.languageId === 'markdown') {
          logger.debug('New editor is markdown, updating outline');
          syncManager.onDocumentChange(editor.document);
        } else {
          logger.debug('New editor is not markdown, clearing outline');
          outlineProvider.clear();
        }
      } else {
        logger.debug('No active editor, clearing outline');
        outlineProvider.clear();
      }
    })
  );

  // Listen for document content changes
  // Sync manager coordinates updates and prevents circular updates via isUpdating flag
  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      const editor = vscode.window.activeTextEditor;
      if (editor && event.document === editor.document && event.document.languageId === 'markdown') {
        syncManager.onDocumentChange(event.document);
      }
    })
  );

  // Initialize with current editor if it's markdown
  logger.debug('Checking for active editor to initialize outline...');
  const editor = vscode.window.activeTextEditor;
  if (editor) {
    logger.debug(`Active editor found: ${editor.document.uri.fsPath}`);
    logger.debug(`Language ID: ${editor.document.languageId}`);
    if (editor.document.languageId === 'markdown') {
      logger.debug('Initializing outline with current markdown document');
      syncManager.onDocumentChange(editor.document);
    } else {
      logger.debug('Active editor is not a markdown file, skipping initialization');
    }
  } else {
    logger.debug('No active editor found, outline will initialize when a markdown file is opened');
  }

  // Register tree view
  logger.debug('Registering tree view for disposal');
  context.subscriptions.push(treeView);

  // Listen for configuration changes to update log level
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration('doctk.logging.level')) {
        logger.updateLogLevel();
        logger.info('Log level updated');
      }
    })
  );

  // Register logger for disposal
  context.subscriptions.push({
    dispose: () => logger.dispose(),
  });

  logger.info('Extension activation complete');
}

/**
 * Execute an operation on a node.
 *
 * @param operation - Operation name
 * @param node - Target node
 */
async function executeOperation(operation: string, node: OutlineNode): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active editor');
    return;
  }

  const document = editor.document;
  if (document.languageId !== 'markdown') {
    vscode.window.showErrorMessage('Current document is not a Markdown file');
    return;
  }

  // Execute operation within sync manager context to prevent circular updates.
  // The sync manager sets isUpdating flag to prevent onDocumentChange from
  // firing while we're applying tree operation changes to the document.
  await syncManager.onTreeViewChange(async () => {
    // Get document text
    const documentText = document.getText();

    // Call Python backend
    let result;
    switch (operation) {
      case 'promote':
        result = await pythonBridge.promote(documentText, node.id);
        break;
      case 'demote':
        result = await pythonBridge.demote(documentText, node.id);
        break;
      case 'move_up':
        result = await pythonBridge.moveUp(documentText, node.id);
        break;
      case 'move_down':
        result = await pythonBridge.moveDown(documentText, node.id);
        break;
      case 'delete':
        result = await pythonBridge.delete(documentText, node.id);
        break;
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }

    if (result.success) {
      // Apply changes to document
      const edit = new vscode.WorkspaceEdit();

      // Use granular edits if available (preferred)
      if (result.modifiedRanges && result.modifiedRanges.length > 0) {
        for (const range of result.modifiedRanges) {
          const vsRange = new vscode.Range(
            new vscode.Position(range.start_line, range.start_column),
            new vscode.Position(range.end_line, range.end_column)
          );
          edit.replace(document.uri, vsRange, range.new_text);
        }
      } else {
        // Fallback to full document replacement
        const fullRange = new vscode.Range(
          document.positionAt(0),
          document.positionAt(documentText.length)
        );
        edit.replace(document.uri, fullRange, result.document || '');
      }

      await vscode.workspace.applyEdit(edit);

      // Update tree view to reflect changes
      outlineProvider.updateFromDocument(document);
    } else {
      throw new Error(result.error || 'Operation failed');
    }
  });
}

/**
 * Deactivate the extension.
 */
export async function deactivate() {
  logger.info('doctk outliner extension is now deactivated');

  // Stop language server
  if (languageClient) {
    await languageClient.stop();
  }

  // Stop Python bridge
  if (pythonBridge) {
    await pythonBridge.stop();
  }
}
