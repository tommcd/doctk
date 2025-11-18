/**
 * Type definitions for the doctk outliner extension.
 */

import { Range } from 'vscode';

/**
 * Metadata associated with an outline node.
 */
export interface NodeMetadata {
  /** Whether the node has body content */
  hasContent: boolean;
  /** Character count of content */
  contentLength: number;
  /** Timestamp of last modification */
  lastModified: number;
}

/**
 * Represents a node in the document outline tree.
 */
export interface OutlineNode {
  /** Unique identifier for the node (e.g., "h1-0", "h2-3") */
  id: string;
  /** Heading text */
  label: string;
  /** Heading level (1-6) */
  level: number;
  /** Position in document */
  range: Range;
  /** Child nodes */
  children: OutlineNode[];
  /** Parent reference (optional) */
  parent?: OutlineNode;
  /** Additional metadata */
  metadata?: NodeMetadata;
}

/**
 * Represents the complete document tree structure.
 */
export interface DocumentTree {
  /** Root node of the tree */
  root: OutlineNode;
  /** Map for fast lookup by ID */
  nodeMap: Map<string, OutlineNode>;
  /** Version number for change tracking */
  version: number;
}

/**
 * Operation types supported by the outliner.
 */
export type OperationType =
  | 'promote'
  | 'demote'
  | 'move_up'
  | 'move_down'
  | 'nest'
  | 'unnest'
  | 'delete';

/**
 * Represents an operation to be performed on a node.
 */
export interface Operation {
  /** Type of operation */
  type: OperationType;
  /** Target node for the operation */
  targetNode: OutlineNode;
  /** Optional parameters for the operation */
  params?: Record<string, any>;
}

/**
 * Result of executing an operation.
 */
export interface OperationResult {
  /** Whether the operation succeeded */
  success: boolean;
  /** Modified document text (if successful) */
  document?: string;
  /** Ranges that were modified */
  modifiedRanges?: Range[];
  /** Error message (if failed) */
  error?: string;
}

/**
 * Result of validating an operation.
 */
export interface ValidationResult {
  /** Whether the operation is valid */
  valid: boolean;
  /** Error message (if invalid) */
  error?: string;
}

/**
 * Configuration for the doctk outliner.
 */
export interface DoctkConfiguration {
  outliner: {
    /** Whether to automatically refresh the tree */
    autoRefresh: boolean;
    /** Delay before refreshing (milliseconds) */
    refreshDelay: number;
    /** Whether to show content preview */
    showContentPreview: boolean;
    /** Maximum length of preview text */
    maxPreviewLength: number;
  };

  lsp: {
    /** Whether LSP is enabled */
    enabled: boolean;
    /** Trace level for LSP communication */
    trace: 'off' | 'messages' | 'verbose';
    /** Maximum number of completion items to show */
    maxCompletionItems: number;
  };

  performance: {
    /** Threshold for considering a document "large" (number of headings) */
    largeDocumentThreshold: number;
    /** Whether to enable virtualization for large documents */
    enableVirtualization: boolean;
  };
}
