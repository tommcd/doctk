/**
 * VS Code extension entry point for doctk outliner.
 */

import * as vscode from 'vscode';
import { DocumentOutlineProvider } from './outlineProvider';
import { PythonBridge } from './pythonBridge';
import { DocumentSyncManager } from './documentSyncManager';
import { OutlineNode } from './types';

let outlineProvider: DocumentOutlineProvider;
let pythonBridge: PythonBridge;
let syncManager: DocumentSyncManager;
let treeView: vscode.TreeView<any>;

/**
 * Activate the extension.
 *
 * @param context - Extension context
 */
export async function activate(context: vscode.ExtensionContext) {
  console.log('doctk outliner extension is now active');

  // Initialize Python bridge first
  const config = vscode.workspace.getConfiguration('doctk');
  pythonBridge = new PythonBridge({
    pythonCommand: config.get('lsp.pythonCommand', 'python3'),
    cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
  });

  try {
    await pythonBridge.start();
    console.log('Python bridge started successfully');
  } catch (error) {
    console.error('Failed to start Python bridge:', error);
    vscode.window.showErrorMessage('Failed to start doctk backend. Some features may not work.');
  }

  // Initialize outline provider with Python bridge for centralized ID generation
  outlineProvider = new DocumentOutlineProvider(pythonBridge);

  // Initialize document synchronization manager
  const config_sync = vscode.workspace.getConfiguration('doctk.outliner');
  const refreshDelay = config_sync.get('refreshDelay', 300);
  syncManager = new DocumentSyncManager(outlineProvider, refreshDelay);

  // Register tree data provider with drag-and-drop support
  treeView = vscode.window.createTreeView('doctkOutline', {
    treeDataProvider: outlineProvider,
    showCollapseAll: true,
    canSelectMany: false,
    dragAndDropController: outlineProvider,
  });

  // Register sync manager for disposal
  context.subscriptions.push({
    dispose: () => syncManager.dispose(),
  });

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.refresh', () => {
      const editor = vscode.window.activeTextEditor;
      if (editor && editor.document.languageId === 'markdown') {
        outlineProvider.updateFromDocument(editor.document);
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
      await executeOperation('promote', node);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.demote', async (node: OutlineNode) => {
      await executeOperation('demote', node);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.moveUp', async (node: OutlineNode) => {
      await executeOperation('move_up', node);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.moveDown', async (node: OutlineNode) => {
      await executeOperation('move_down', node);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.delete', async (node: OutlineNode) => {
      await executeOperation('delete', node);
    })
  );

  // Listen for active editor changes
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor && editor.document.languageId === 'markdown') {
        syncManager.onDocumentChange(editor.document);
      } else {
        outlineProvider.clear();
      }
    })
  );

  // Listen for document changes
  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      const editor = vscode.window.activeTextEditor;
      if (editor && event.document === editor.document && event.document.languageId === 'markdown') {
        syncManager.onDocumentChange(event.document);
      }
    })
  );

  // Listen for external file changes (Requirement 16.5)
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      // Check if this save was triggered externally (not by our extension)
      const editor = vscode.window.activeTextEditor;
      if (
        editor &&
        document === editor.document &&
        document.languageId === 'markdown' &&
        !syncManager.isCurrentlyUpdating()
      ) {
        // Treat as potential external change
        syncManager.onExternalChange(document);
      }
    })
  );

  // Initialize with current editor if it's markdown
  const editor = vscode.window.activeTextEditor;
  if (editor && editor.document.languageId === 'markdown') {
    syncManager.onDocumentChange(editor.document);
  }

  // Register tree view
  context.subscriptions.push(treeView);
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

  // Wrap operation in sync manager to prevent circular updates
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

      // Update tree view (sync manager handles preventing circular updates)
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
  console.log('doctk outliner extension is now deactivated');

  // Stop Python bridge
  if (pythonBridge) {
    await pythonBridge.stop();
  }
}
