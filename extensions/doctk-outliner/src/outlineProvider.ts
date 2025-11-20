/**
 * Document outline provider for VS Code tree view.
 *
 * ## Performance Optimizations
 *
 * ### Virtual Scrolling (Automatic)
 * VS Code's TreeView provides automatic virtualization - only visible tree items
 * are rendered in the DOM. This happens automatically through the TreeDataProvider
 * interface and requires no manual implementation. The TreeView efficiently handles
 * documents with thousands of nodes by rendering only what's currently visible.
 *
 * ### Lazy Loading (Implemented)
 * For large documents (configurable threshold, default 1000 headings), the tree
 * starts with nodes in a collapsed state. VS Code only calls getChildren() when
 * a node is expanded, enabling on-demand loading. This significantly improves
 * initial rendering performance for large documents.
 *
 * Configuration:
 * - doctk.performance.largeDocumentThreshold: Number of headings to trigger optimizations
 * - doctk.performance.enableLazyLoading: Enable/disable lazy loading behavior
 */

import * as vscode from 'vscode';
import { OutlineNode, DocumentTree, BackendTreeNode } from './types';
import { PythonBridge } from './pythonBridge';
import { getLogger } from './logger';

const logger = getLogger();

/**
 * Provides a tree view of document structure with drag-and-drop support.
 *
 * Implements VS Code's TreeDataProvider and TreeDragAndDropController interfaces
 * to display document headings in a hierarchical tree view with interactive
 * drag-and-drop operations for restructuring documents.
 *
 * Performance: Optimized for documents with 1000+ headings through automatic
 * virtualization (VS Code built-in) and lazy loading (collapsible state management).
 */
export class DocumentOutlineProvider
  implements
    vscode.TreeDataProvider<OutlineNode>,
    vscode.TreeDragAndDropController<OutlineNode>
{
  private _onDidChangeTreeData: vscode.EventEmitter<OutlineNode | undefined | null | void> =
    new vscode.EventEmitter<OutlineNode | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<OutlineNode | undefined | null | void> =
    this._onDidChangeTreeData.event;

  // Drag-and-drop configuration
  readonly dragMimeTypes = ['application/vnd.code.tree.doctkOutline'];
  readonly dropMimeTypes = ['application/vnd.code.tree.doctkOutline'];

  private documentTree: DocumentTree | null = null;
  private document: vscode.TextDocument | null = null;
  private debounceTimer: NodeJS.Timeout | null = null;
  private pythonBridge: PythonBridge | null = null;
  // Cache the large document check result to avoid repeated calculations during rendering
  // This is computed once in updateFromDocument() and reused in getTreeItem()
  private isLargeDoc: boolean = false;

  constructor(pythonBridge?: PythonBridge) {
    this.pythonBridge = pythonBridge || null;
  }

  /**
   * Get the configured debounce delay from VS Code settings.
   * Falls back to default if not configured.
   */
  private getDebounceDelay(): number {
    const config = vscode.workspace.getConfiguration('doctk.outliner');
    return config.get('refreshDelay', 300); // Default: 300ms
  }

  /**
   * Compute and cache whether the current document is "large" based on heading count.
   * Large documents use performance optimizations like lazy loading.
   *
   * This method should be called once after the tree is built in updateFromDocument().
   * The cached result is then used by getTreeItem() to avoid repeated calculations.
   */
  private computeIsLargeDocument(): void {
    if (!this.documentTree) {
      this.isLargeDoc = false;
      return;
    }

    const config = vscode.workspace.getConfiguration('doctk.performance');
    const threshold = config.get('largeDocumentThreshold', 1000);
    const enableLazyLoading = config.get('enableLazyLoading', true);

    if (!enableLazyLoading) {
      this.isLargeDoc = false;
      return;
    }

    // Count total nodes in tree
    const totalNodes = this.documentTree.nodeMap.size;
    this.isLargeDoc = totalNodes >= threshold;
  }

  /**
   * Get tree item representation for a node.
   *
   * @param element - The outline node
   * @returns TreeItem for display in the tree view
   */
  getTreeItem(element: OutlineNode): vscode.TreeItem {
    logger.debug(`getTreeItem called for node: ${element.id} (${element.label})`);

    // Determine collapsible state based on document size
    // For large documents, start nodes collapsed to enable lazy loading
    // For normal documents, start nodes expanded for convenience
    // Use cached isLargeDoc to avoid redundant calculations (computed in updateFromDocument)
    let collapsibleState: vscode.TreeItemCollapsibleState;
    if (element.children.length > 0) {
      collapsibleState = this.isLargeDoc
        ? vscode.TreeItemCollapsibleState.Collapsed
        : vscode.TreeItemCollapsibleState.Expanded;
    } else {
      collapsibleState = vscode.TreeItemCollapsibleState.None;
    }

    const treeItem = new vscode.TreeItem(element.label, collapsibleState);

    // Set description to show level
    treeItem.description = `h${element.level}`;

    // Set icon based on level
    treeItem.iconPath = new vscode.ThemeIcon(this.getIconForLevel(element.level));

    // Set command to navigate to node location
    treeItem.command = {
      command: 'doctk.navigateToNode',
      title: 'Navigate to Node',
      arguments: [element],
    };

    // Store node ID in context value for commands
    treeItem.contextValue = `outlineNode-${element.id}`;

    // Set tooltip with metadata
    if (element.metadata) {
      const lines = [
        `Level: ${element.level}`,
        `ID: ${element.id}`,
        `Range: ${element.range.start.line}:${element.range.start.character} - ${element.range.end.line}:${element.range.end.character}`,
      ];
      if (element.metadata.hasContent) {
        lines.push(`Content length: ${element.metadata.contentLength} chars`);
      }
      treeItem.tooltip = lines.join('\n');
    }

    return treeItem;
  }

  /**
   * Get children of a node.
   *
   * @param element - The parent node, or undefined for root
   * @returns Array of child nodes
   */
  getChildren(element?: OutlineNode): vscode.ProviderResult<OutlineNode[]> {
    logger.debug(`getChildren called for element: ${element ? element.id + ' (' + element.label + ')' : 'root'}`);

    if (!this.documentTree) {
      logger.debug('No document tree available, returning empty array');
      return [];
    }

    if (element) {
      logger.debug(`Returning ${element.children.length} children for ${element.id}`);
      return element.children;
    } else {
      // Return root-level children
      logger.debug(`Returning ${this.documentTree.root.children.length} root-level children`);
      return this.documentTree.root.children;
    }
  }

  /**
   * Get parent of a node.
   *
   * @param element - The child node
   * @returns Parent node or undefined
   */
  getParent(element: OutlineNode): vscode.ProviderResult<OutlineNode> {
    return element.parent;
  }

  /**
   * Refresh the tree view.
   */
  refresh(): void {
    logger.debug('refresh() called - firing onDidChangeTreeData event');
    this._onDidChangeTreeData.fire();
    logger.debug('onDidChangeTreeData event fired');
  }

  /**
   * Update the tree from the current document.
   *
   * @param document - The text document to parse
   */
  updateFromDocument(document: vscode.TextDocument): void {
    logger.debug(`updateFromDocument called for: ${document.uri.fsPath}`);

    // Debounce updates to prevent excessive refreshes
    if (this.debounceTimer) {
      logger.debug('Clearing existing debounce timer');
      clearTimeout(this.debounceTimer);
    }

    logger.debug(`Setting debounce timer (${this.getDebounceDelay()}ms)`);
    this.debounceTimer = setTimeout(async () => {
      logger.debug('Debounce timer fired, updating document tree');
      this.document = document;

      // Try to use backend tree with centralized IDs if bridge is available
      if (this.pythonBridge && this.pythonBridge.isRunning()) {
        logger.debug('Python bridge is available, requesting document tree from backend');
        try {
          const documentText = document.getText();
          logger.debug(`Document text length: ${documentText.length} characters`);
          const treeResponse = await this.pythonBridge.getDocumentTree(documentText);
          logger.debug('Received tree response from backend:', treeResponse);
          this.documentTree = this.deserializeBackendTree(treeResponse.root, document, treeResponse.version);
          logger.debug(`Document tree built: ${this.documentTree.nodeMap.size} nodes`);
          // Compute and cache the large document flag once after tree is built
          this.computeIsLargeDocument();
          logger.debug(`Large document: ${this.isLargeDoc}`);
          logger.debug('Calling refresh() to update tree view');
          this.refresh();
          return;
        } catch (error) {
          logger.warn('Failed to get tree from backend, falling back to local parsing:', error);
          // Fall through to local parsing
        }
      } else {
        logger.debug('Python bridge not available or not running, using local parsing');
      }

      // Fallback to local parsing if backend is unavailable
      logger.debug('Parsing document locally');
      this.documentTree = this.parseDocument(document);
      logger.debug(`Document tree built locally: ${this.documentTree.nodeMap.size} nodes`);
      // Compute and cache the large document flag once after tree is built
      this.computeIsLargeDocument();
      logger.debug(`Large document: ${this.isLargeDoc}`);
      logger.debug('Calling refresh() to update tree view');
      this.refresh();
    }, this.getDebounceDelay());
  }

  /**
   * Deserialize backend tree into frontend OutlineNode format.
   *
   * Converts the backend TreeNode structure (with line/column positions)
   * into the frontend OutlineNode structure (with VS Code Ranges).
   *
   * @param backendNode - Backend tree node
   * @param document - VS Code text document for creating ranges
   * @param version - Tree version number
   * @returns DocumentTree structure
   */
  private deserializeBackendTree(
    backendNode: BackendTreeNode,
    document: vscode.TextDocument,
    version: number
  ): DocumentTree {
    const nodeMap = new Map<string, OutlineNode>();

    // Convert backend node to outline node
    const convertNode = (bNode: BackendTreeNode, parentNode?: OutlineNode): OutlineNode => {
      // Create range from line/column positions
      // Warn if backend returns out-of-bounds line numbers
      if (bNode.line >= document.lineCount) {
        logger.warn(
          `Backend returned out-of-bounds line number: ${bNode.line} for node "${bNode.label}". ` +
          `Document has ${document.lineCount} lines. Clamping to last line.`
        );
      }
      const line = Math.min(bNode.line, document.lineCount - 1);
      const lineText = document.lineAt(line).text;
      const endColumn = lineText.length;

      // Clamp column to prevent out-of-bounds access
      const column = Math.min(bNode.column, lineText.length);

      const range = new vscode.Range(
        new vscode.Position(line, column),
        new vscode.Position(line, endColumn)
      );

      // Create outline node
      const outlineNode: OutlineNode = {
        id: bNode.id,
        label: bNode.label,
        level: bNode.level,
        range,
        children: [],
        parent: parentNode,
        // Note: Metadata is not provided by backend and would require
        // document content analysis to calculate accurately. Omitted to
        // avoid displaying incorrect placeholder values in tooltips.
        // TODO: Consider calculating content metadata from document ranges
      };

      // Add to node map (skip root node)
      if (bNode.id !== 'root') {
        nodeMap.set(bNode.id, outlineNode);
      }

      // Recursively convert children
      for (const bChild of bNode.children) {
        const childNode = convertNode(bChild, outlineNode);
        outlineNode.children.push(childNode);
      }

      return outlineNode;
    };

    // Convert the tree starting from root
    const root = convertNode(backendNode);

    return {
      root,
      nodeMap,
      version,
    };
  }

  /**
   * Parse a document to build the outline tree (local fallback).
   *
   * This method is used as a fallback when the backend is unavailable.
   * It performs local ID generation which may differ from backend IDs.
   *
   * @param document - The text document to parse
   * @returns DocumentTree structure
   */
  private parseDocument(document: vscode.TextDocument): DocumentTree {
    const root: OutlineNode = {
      id: 'root',
      label: 'Document',
      level: 0,
      range: new vscode.Range(0, 0, 0, 0),
      children: [],
    };

    const nodeMap = new Map<string, OutlineNode>();
    const stack: OutlineNode[] = [root];
    const headingCounters = new Map<number, number>();

    // Parse document line by line
    for (let i = 0; i < document.lineCount; i++) {
      const line = document.lineAt(i);
      const text = line.text;

      // Match Markdown heading pattern (# Heading)
      const headingMatch = text.match(/^(#{1,6})\s+(.+)$/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const label = headingMatch[2].trim();

        // Generate unique ID
        const count = headingCounters.get(level) || 0;
        headingCounters.set(level, count + 1);
        const id = `h${level}-${count}`;

        // Create node
        const node: OutlineNode = {
          id,
          label,
          level,
          range: line.range,
          children: [],
          metadata: {
            hasContent: false,
            contentLength: 0,
            lastModified: Date.now(),
          },
        };

        // Find parent in stack
        // Pop stack until we find a node with level < current level
        while (stack.length > 0 && stack[stack.length - 1].level >= level) {
          stack.pop();
        }

        if (stack.length > 0) {
          const parent = stack[stack.length - 1];
          node.parent = parent;
          parent.children.push(node);
        }

        // Push current node to stack
        stack.push(node);
        nodeMap.set(id, node);
      }
    }

    return {
      root,
      nodeMap,
      version: 1,
    };
  }

  /**
   * Get icon name for heading level.
   *
   * @param level - Heading level (1-6)
   * @returns Icon name
   */
  private getIconForLevel(level: number): string {
    const icons = [
      'symbol-class', // h1
      'symbol-method', // h2
      'symbol-property', // h3
      'symbol-field', // h4
      'symbol-variable', // h5
      'symbol-constant', // h6
    ];
    return icons[level - 1] || 'symbol-misc';
  }

  /**
   * Get node by ID.
   *
   * @param nodeId - Node ID to find
   * @returns OutlineNode or undefined
   */
  getNodeById(nodeId: string): OutlineNode | undefined {
    return this.documentTree?.nodeMap.get(nodeId);
  }

  /**
   * Get the current document tree.
   *
   * @returns DocumentTree or null
   */
  getDocumentTree(): DocumentTree | null {
    return this.documentTree;
  }

  /**
   * Get the current document.
   *
   * @returns TextDocument or null
   */
  getDocument(): vscode.TextDocument | null {
    return this.document;
  }

  /**
   * Clear the tree view.
   */
  clear(): void {
    logger.debug('clear() called - clearing document tree');
    this.documentTree = null;
    this.document = null;
    this.isLargeDoc = false;
    this.refresh();
  }

  /**
   * Handle drag operation.
   *
   * Captures the source nodes being dragged and stores them in the data transfer.
   *
   * @param source - Array of nodes being dragged
   * @param dataTransfer - Data transfer object for storing drag data
   * @param token - Cancellation token
   */
  handleDrag(
    source: readonly OutlineNode[],
    dataTransfer: vscode.DataTransfer,
    _token: vscode.CancellationToken
  ): void {
    // Store the source node IDs as JSON
    const nodeIds = source.map((node) => node.id);
    dataTransfer.set(
      'application/vnd.code.tree.doctkOutline',
      new vscode.DataTransferItem(JSON.stringify(nodeIds))
    );
  }

  /**
   * Handle drop operation.
   *
   * Determines the type of drop (nest or reorder) and executes the appropriate operation.
   *
   * @param target - Target node where items are dropped (undefined for root)
   * @param dataTransfer - Data transfer object containing drag data
   * @param token - Cancellation token
   */
  async handleDrop(
    target: OutlineNode | undefined,
    dataTransfer: vscode.DataTransfer,
    token: vscode.CancellationToken
  ): Promise<void> {
    // Check cancellation
    if (token.isCancellationRequested) {
      return;
    }

    // Get the dragged node IDs
    const transferItem = dataTransfer.get('application/vnd.code.tree.doctkOutline');
    if (!transferItem) {
      vscode.window.showErrorMessage('Invalid drop data');
      return;
    }

    // Validate type before parsing
    if (typeof transferItem.value !== 'string') {
      vscode.window.showErrorMessage('Invalid drop data type');
      return;
    }

    let nodeIds: string[];
    try {
      const parsed = JSON.parse(transferItem.value);
      if (!Array.isArray(parsed)) {
        vscode.window.showErrorMessage('Invalid drop data: expected array');
        return;
      }
      nodeIds = parsed;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      vscode.window.showErrorMessage(`Failed to parse drop data: ${errorMsg}`);
      return;
    }

    if (nodeIds.length === 0) {
      return;
    }

    // For now, only support single-node drag-and-drop
    if (nodeIds.length > 1) {
      vscode.window.showWarningMessage('Multiple node drag-and-drop not yet supported');
      return;
    }

    const sourceId = nodeIds[0];

    // Get the source node
    const sourceNode = this.getNodeById(sourceId);
    if (!sourceNode) {
      vscode.window.showErrorMessage(`Source node not found: ${sourceId}`);
      return;
    }

    // Validate drop: can't drop a node onto itself or its descendants
    if (target && this.isDescendant(sourceNode, target)) {
      vscode.window.showErrorMessage('Cannot drop a node onto itself or its descendants');
      return;
    }

    // Determine drop type and execute operation
    await this.executeDropOperation(sourceNode, target);
  }

  /**
   * Execute the appropriate operation based on drop target.
   *
   * @param source - Source node being dropped
   * @param target - Target node where source is dropped (undefined for root)
   */
  private async executeDropOperation(
    source: OutlineNode,
    target: OutlineNode | undefined
  ): Promise<void> {
    if (!this.document || !this.pythonBridge) {
      vscode.window.showErrorMessage('No active document or Python bridge not available');
      return;
    }

    try {
      const documentText = this.document.getText();
      let result;

      if (!target) {
        // Drop at root level - unnest the node to make it a top-level heading
        // Note: VS Code's TreeDragAndDropController doesn't provide drop position
        // (before/after), so we can only unnest to top level, not reorder precisely
        result = await this.pythonBridge.unnest(documentText, source.id);
      } else {
        // Drop onto a target node - this nests the source under the target
        result = await this.pythonBridge.nest(documentText, source.id, target.id);
      }

      if (result.success) {
        // Apply changes to document
        const edit = new vscode.WorkspaceEdit();

        // Use granular edits if available
        if (result.modifiedRanges && result.modifiedRanges.length > 0) {
          for (const range of result.modifiedRanges) {
            const vsRange = new vscode.Range(
              new vscode.Position(range.start_line, range.start_column),
              new vscode.Position(range.end_line, range.end_column)
            );
            edit.replace(this.document.uri, vsRange, range.new_text);
          }
        } else {
          // Fallback to full document replacement
          const fullRange = new vscode.Range(
            this.document.positionAt(0),
            this.document.positionAt(documentText.length)
          );
          edit.replace(this.document.uri, fullRange, result.document || '');
        }

        // Apply edit and verify success
        const editSucceeded = await vscode.workspace.applyEdit(edit);
        if (!editSucceeded) {
          vscode.window.showErrorMessage('Failed to apply document changes');
          return;
        }

        // Update tree view only if edit succeeded
        this.updateFromDocument(this.document);

        // Show appropriate success message based on operation type
        if (!target) {
          vscode.window.showInformationMessage(
            `Moved "${source.label}" to top level. Use move operations to adjust position.`
          );
        } else {
          vscode.window.showInformationMessage(
            `Moved "${source.label}" under "${target.label}"`
          );
        }
      } else {
        vscode.window.showErrorMessage(`Drop operation failed: ${result.error}`);
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      vscode.window.showErrorMessage(`Error during drop: ${errorMsg}`);
      logger.error('Drop error:', error);
    }
  }

  /**
   * Check if a node is a descendant of another node.
   *
   * @param ancestor - Potential ancestor node
   * @param node - Node to check
   * @returns True if node is a descendant of ancestor
   */
  private isDescendant(ancestor: OutlineNode, node: OutlineNode): boolean {
    if (ancestor.id === node.id) {
      return true;
    }

    for (const child of ancestor.children) {
      if (this.isDescendant(child, node)) {
        return true;
      }
    }

    return false;
  }
}
