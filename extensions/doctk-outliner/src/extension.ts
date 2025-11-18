/**
 * VS Code extension entry point for doctk outliner.
 */

import * as vscode from 'vscode';
import { DocumentOutlineProvider } from './outlineProvider';
import { PythonBridge } from './pythonBridge';

let outlineProvider: DocumentOutlineProvider;
let pythonBridge: PythonBridge;
let treeView: vscode.TreeView<any>;

/**
 * Activate the extension.
 *
 * @param context - Extension context
 */
export async function activate(context: vscode.ExtensionContext) {
  console.log('doctk outliner extension is now active');

  // Initialize outline provider
  outlineProvider = new DocumentOutlineProvider();

  // Register tree data provider
  treeView = vscode.window.createTreeView('doctkOutline', {
    treeDataProvider: outlineProvider,
    showCollapseAll: true,
  });

  // Initialize Python bridge
  pythonBridge = new PythonBridge({
    cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
  });

  try {
    await pythonBridge.start();
    console.log('Python bridge started successfully');
  } catch (error) {
    console.error('Failed to start Python bridge:', error);
    vscode.window.showErrorMessage('Failed to start doctk backend. Some features may not work.');
  }

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
    vscode.commands.registerCommand('doctk.navigateToNode', (node: any) => {
      const editor = vscode.window.activeTextEditor;
      if (editor && node.range) {
        editor.selection = new vscode.Selection(node.range.start, node.range.end);
        editor.revealRange(node.range, vscode.TextEditorRevealType.InCenter);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.promote', async (node: any) => {
      await executeOperation('promote', node);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.demote', async (node: any) => {
      await executeOperation('demote', node);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.moveUp', async (node: any) => {
      await executeOperation('move_up', node);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.moveDown', async (node: any) => {
      await executeOperation('move_down', node);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('doctk.delete', async (node: any) => {
      // Delete operation would need to be implemented
      vscode.window.showInformationMessage('Delete operation not yet implemented');
    })
  );

  // Listen for active editor changes
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor && editor.document.languageId === 'markdown') {
        outlineProvider.updateFromDocument(editor.document);
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
        outlineProvider.updateFromDocument(event.document);
      }
    })
  );

  // Initialize with current editor if it's markdown
  const editor = vscode.window.activeTextEditor;
  if (editor && editor.document.languageId === 'markdown') {
    outlineProvider.updateFromDocument(editor.document);
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
async function executeOperation(operation: string, node: any): Promise<void> {
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

  try {
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
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }

    if (result.success) {
      // Apply changes to document
      const edit = new vscode.WorkspaceEdit();
      const fullRange = new vscode.Range(
        document.positionAt(0),
        document.positionAt(documentText.length)
      );
      edit.replace(document.uri, fullRange, result.document);
      await vscode.workspace.applyEdit(edit);

      // Update tree view
      outlineProvider.updateFromDocument(document);
    } else {
      vscode.window.showErrorMessage(`Operation failed: ${result.error}`);
    }
  } catch (error) {
    vscode.window.showErrorMessage(`Error executing operation: ${error}`);
    console.error('Operation error:', error);
  }
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
