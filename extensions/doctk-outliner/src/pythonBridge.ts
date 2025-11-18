/**
 * Python bridge for executing document operations via JSON-RPC.
 */

import { spawn, ChildProcess } from 'child_process';
import { OperationResult, ValidationResult, DocumentTreeResponse } from './types';

interface JsonRpcRequest {
  jsonrpc: '2.0';
  id: number;
  method: string;
  params: Record<string, any>;
}

interface JsonRpcResponse {
  jsonrpc: '2.0';
  id: number;
  result?: any;
  error?: {
    code: number;
    message: string;
  };
}

interface PendingRequest {
  resolve: (value: any) => void;
  reject: (error: Error) => void;
}

/**
 * Options for configuring the Python bridge.
 */
export interface PythonBridgeOptions {
  /** Path to the Python executable (defaults to 'python3') */
  pythonCommand?: string;
  /** Working directory for the Python process */
  cwd?: string;
  /** Timeout for requests in milliseconds (default: 10000) */
  timeout?: number;
  /** Maximum number of restart attempts (default: 3) */
  maxRestarts?: number;
}

/**
 * Bridge to Python backend for executing document operations.
 *
 * Communicates via JSON-RPC over stdin/stdout with a Python process.
 */
export class PythonBridge {
  private process: ChildProcess | null = null;
  private nextId = 1;
  private pendingRequests = new Map<number, PendingRequest>();
  private buffer = '';
  private options: Required<PythonBridgeOptions>;
  private restartCount = 0;
  private isStarting = false;
  private isStopping = false;

  constructor(options: PythonBridgeOptions = {}) {
    this.options = {
      pythonCommand: options.pythonCommand || 'python3',
      cwd: options.cwd || process.cwd(),
      timeout: options.timeout || 10000,
      maxRestarts: options.maxRestarts || 3,
    };
  }

  /**
   * Start the Python bridge process.
   */
  async start(): Promise<void> {
    if (this.process || this.isStarting) {
      return;
    }

    this.isStarting = true;

    try {
      // Spawn Python process with uv run
      const args =
        this.options.pythonCommand === 'uv'
          ? ['run', 'python', '-m', 'doctk.lsp.bridge']
          : ['-m', 'doctk.lsp.bridge'];

      this.process = spawn(this.options.pythonCommand, args, {
        cwd: this.options.cwd,
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      // Set up event handlers
      this.setupEventHandlers();

      // Wait for process to be ready
      await this.waitForReady();
    } finally {
      this.isStarting = false;
    }
  }

  /**
   * Stop the Python bridge process.
   */
  async stop(): Promise<void> {
    if (!this.process || this.isStopping) {
      return;
    }

    this.isStopping = true;

    try {
      // Reject all pending requests
      for (const [_id, pending] of this.pendingRequests) {
        pending.reject(new Error('Bridge stopped'));
      }
      this.pendingRequests.clear();

      // Kill the process
      if (this.process) {
        this.process.kill();
        this.process = null;
      }
    } finally {
      this.isStopping = false;
    }
  }

  /**
   * Restart the Python bridge process.
   */
  async restart(): Promise<void> {
    await this.stop();
    await this.start();
  }

  /**
   * Call a method on the Python backend.
   *
   * @param method - Method name
   * @param params - Method parameters
   * @returns Promise that resolves with the result
   */
  async call<T = any>(method: string, params: Record<string, any> = {}): Promise<T> {
    if (!this.process) {
      throw new Error('Bridge not started');
    }

    const id = this.nextId++;
    const request: JsonRpcRequest = {
      jsonrpc: '2.0',
      id,
      method,
      params,
    };

    return new Promise((resolve, reject) => {
      // Set up timeout
      const timeoutId = setTimeout(() => {
        this.pendingRequests.delete(id);
        reject(new Error(`Request timed out after ${this.options.timeout}ms`));
      }, this.options.timeout);

      // Store pending request
      this.pendingRequests.set(id, {
        resolve: (value: any) => {
          clearTimeout(timeoutId);
          resolve(value);
        },
        reject: (error: Error) => {
          clearTimeout(timeoutId);
          reject(error);
        },
      });

      // Send request
      const requestLine = JSON.stringify(request) + '\n';
      this.process!.stdin!.write(requestLine);
    });
  }

  /**
   * Execute a promote operation.
   */
  async promote(document: string, nodeId: string): Promise<OperationResult> {
    return this.call<OperationResult>('promote', { document, node_id: nodeId });
  }

  /**
   * Execute a demote operation.
   */
  async demote(document: string, nodeId: string): Promise<OperationResult> {
    return this.call<OperationResult>('demote', { document, node_id: nodeId });
  }

  /**
   * Execute a move_up operation.
   */
  async moveUp(document: string, nodeId: string): Promise<OperationResult> {
    return this.call<OperationResult>('move_up', { document, node_id: nodeId });
  }

  /**
   * Execute a move_down operation.
   */
  async moveDown(document: string, nodeId: string): Promise<OperationResult> {
    return this.call<OperationResult>('move_down', { document, node_id: nodeId });
  }

  /**
   * Execute a nest operation.
   */
  async nest(document: string, nodeId: string, parentId: string): Promise<OperationResult> {
    return this.call<OperationResult>('nest', { document, node_id: nodeId, parent_id: parentId });
  }

  /**
   * Execute an unnest operation.
   */
  async unnest(document: string, nodeId: string): Promise<OperationResult> {
    return this.call<OperationResult>('unnest', { document, node_id: nodeId });
  }

  /**
   * Execute a delete operation.
   */
  async delete(document: string, nodeId: string): Promise<OperationResult> {
    return this.call<OperationResult>('delete', { document, node_id: nodeId });
  }

  /**
   * Validate a promote operation.
   */
  async validatePromote(document: string, nodeId: string): Promise<ValidationResult> {
    return this.call<ValidationResult>('validate_promote', { document, node_id: nodeId });
  }

  /**
   * Validate a demote operation.
   */
  async validateDemote(document: string, nodeId: string): Promise<ValidationResult> {
    return this.call<ValidationResult>('validate_demote', { document, node_id: nodeId });
  }

  /**
   * Validate a delete operation.
   */
  async validateDelete(document: string, nodeId: string): Promise<ValidationResult> {
    return this.call<ValidationResult>('validate_delete', { document, node_id: nodeId });
  }

  /**
   * Get the document tree with backend-assigned node IDs.
   *
   * This method calls the backend to build the document tree structure
   * with centralized ID generation, ensuring consistency across operations.
   *
   * @param document - Document text
   * @returns Document tree structure with centralized IDs
   */
  async getDocumentTree(document: string): Promise<DocumentTreeResponse> {
    return this.call<DocumentTreeResponse>('get_document_tree', { document });
  }

  /**
   * Set up event handlers for the Python process.
   */
  private setupEventHandlers(): void {
    if (!this.process) {
      return;
    }

    // Handle stdout data (responses)
    this.process.stdout!.on('data', (data: Buffer) => {
      this.handleStdout(data.toString());
    });

    // Handle stderr data (errors)
    this.process.stderr!.on('data', (data: Buffer) => {
      console.error('Python bridge error:', data.toString());
    });

    // Handle process exit
    this.process.on('exit', (code: number | null, signal: string | null) => {
      console.log(`Python bridge exited with code ${code}, signal ${signal}`);
      this.handleProcessExit(code, signal);
    });

    // Handle process error
    this.process.on('error', (error: Error) => {
      console.error('Python bridge process error:', error);
      this.handleProcessError(error);
    });
  }

  /**
   * Handle stdout data from the Python process.
   */
  private handleStdout(data: string): void {
    // Add data to buffer
    this.buffer += data;

    // Process complete lines
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.trim()) {
        try {
          const response: JsonRpcResponse = JSON.parse(line);
          this.handleResponse(response);
        } catch (error) {
          console.error('Failed to parse response:', error, line);
        }
      }
    }
  }

  /**
   * Handle a JSON-RPC response.
   */
  private handleResponse(response: JsonRpcResponse): void {
    const pending = this.pendingRequests.get(response.id);
    if (!pending) {
      console.warn('Received response for unknown request:', response.id);
      return;
    }

    this.pendingRequests.delete(response.id);

    if (response.error) {
      pending.reject(new Error(response.error.message));
    } else {
      pending.resolve(response.result);
    }
  }

  /**
   * Handle process exit.
   */
  private async handleProcessExit(code: number | null, signal: string | null): Promise<void> {
    // Reject all pending requests
    for (const [_id, pending] of this.pendingRequests) {
      pending.reject(new Error(`Process exited with code ${code}, signal ${signal}`));
    }
    this.pendingRequests.clear();

    // Attempt restart if not stopping
    if (!this.isStopping && this.restartCount < this.options.maxRestarts) {
      console.log(`Attempting to restart Python bridge (attempt ${this.restartCount + 1})`);
      this.restartCount++;

      try {
        await this.restart();
        this.restartCount = 0; // Reset counter on successful restart
      } catch (error) {
        console.error('Failed to restart Python bridge:', error);
      }
    }
  }

  /**
   * Handle process error.
   */
  private handleProcessError(error: Error): void {
    // Reject all pending requests
    for (const [_id, pending] of this.pendingRequests) {
      pending.reject(error);
    }
    this.pendingRequests.clear();
  }

  /**
   * Wait for the process to be ready.
   */
  private async waitForReady(): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Bridge process failed to start within timeout'));
      }, 5000); // 5 second timeout

      const onData = (data: Buffer) => {
        const output = data.toString();
        if (output.includes('BRIDGE_READY')) {
          clearTimeout(timeout);
          // Remove the data listener since we got the ready signal
          this.process!.stdout!.removeListener('data', onData);
          resolve();
        }
      };

      this.process!.stdout!.on('data', onData);
    });
  }

  /**
   * Check if the bridge is running.
   */
  isRunning(): boolean {
    return this.process !== null && !this.process.killed;
  }
}
