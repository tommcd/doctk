/**
 * Document outline provider for VS Code tree view.
 */

import * as vscode from 'vscode';
import { OutlineNode, DocumentTree, BackendTreeNode } from './types';
import { PythonBridge } from './pythonBridge';

/**
 * Provides a tree view of document structure.
 *
 * Implements VS Code's TreeDataProvider interface to display
 * document headings in a hierarchical tree view.
 */
export class DocumentOutlineProvider implements vscode.TreeDataProvider<OutlineNode> {
  private _onDidChangeTreeData: vscode.EventEmitter<OutlineNode | undefined | null | void> =
    new vscode.EventEmitter<OutlineNode | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<OutlineNode | undefined | null | void> =
    this._onDidChangeTreeData.event;

  private documentTree: DocumentTree | null = null;
  private document: vscode.TextDocument | null = null;
  private debounceTimer: NodeJS.Timeout | null = null;
  private readonly debounceDelay = 300; // milliseconds
  private pythonBridge: PythonBridge | null = null;

  constructor(pythonBridge?: PythonBridge) {
    this.pythonBridge = pythonBridge || null;
  }

  /**
   * Get tree item representation for a node.
   *
   * @param element - The outline node
   * @returns TreeItem for display in the tree view
   */
  getTreeItem(element: OutlineNode): vscode.TreeItem {
    const treeItem = new vscode.TreeItem(
      element.label,
      element.children.length > 0
        ? vscode.TreeItemCollapsibleState.Expanded
        : vscode.TreeItemCollapsibleState.None
    );

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
    if (!this.documentTree) {
      return [];
    }

    if (element) {
      return element.children;
    } else {
      // Return root-level children
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
    this._onDidChangeTreeData.fire();
  }

  /**
   * Update the tree from the current document.
   *
   * @param document - The text document to parse
   */
  updateFromDocument(document: vscode.TextDocument): void {
    // Debounce updates to prevent excessive refreshes
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    this.debounceTimer = setTimeout(async () => {
      this.document = document;

      // Try to use backend tree with centralized IDs if bridge is available
      if (this.pythonBridge && this.pythonBridge.isRunning()) {
        try {
          const documentText = document.getText();
          const treeResponse = await this.pythonBridge.getDocumentTree(documentText);
          this.documentTree = this.deserializeBackendTree(treeResponse.root, document, treeResponse.version);
          this.refresh();
          return;
        } catch (error) {
          console.warn('Failed to get tree from backend, falling back to local parsing:', error);
          // Fall through to local parsing
        }
      }

      // Fallback to local parsing if backend is unavailable
      this.documentTree = this.parseDocument(document);
      this.refresh();
    }, this.debounceDelay);
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
   * @param parent - Parent outline node (for setting parent references)
   * @returns DocumentTree structure
   */
  private deserializeBackendTree(
    backendNode: BackendTreeNode,
    document: vscode.TextDocument,
    version: number,
    parent?: OutlineNode
  ): DocumentTree {
    const nodeMap = new Map<string, OutlineNode>();

    // Convert backend node to outline node
    const convertNode = (bNode: BackendTreeNode, parentNode?: OutlineNode): OutlineNode => {
      // Create range from line/column positions
      const line = Math.min(bNode.line, document.lineCount - 1);
      const lineText = document.lineAt(line).text;
      const endColumn = lineText.length;

      const range = new vscode.Range(
        new vscode.Position(bNode.line, bNode.column),
        new vscode.Position(bNode.line, endColumn)
      );

      // Create outline node
      const outlineNode: OutlineNode = {
        id: bNode.id,
        label: bNode.label,
        level: bNode.level,
        range,
        children: [],
        parent: parentNode,
        metadata: {
          hasContent: false,
          contentLength: 0,
          lastModified: Date.now(),
        },
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
    let headingCounters = new Map<number, number>();

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
    this.documentTree = null;
    this.document = null;
    this.refresh();
  }
}
