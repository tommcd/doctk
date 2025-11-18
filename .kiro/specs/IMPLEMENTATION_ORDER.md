# Implementation Order and Dependencies

This document describes the dependencies between the three specs and the recommended implementation order.

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                     doctk Core API                           │
│                  (External Dependency)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ depends on
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              doctk-core-integration                          │
│  - StructureOperations (promote, demote, etc.)              │
│  - ExtensionBridge (JSON-RPC server)                        │
│  - OperationRegistry (for LSP)                              │
│  - REPL, ScriptExecutor                                     │
└────────┬────────────────────────────┬───────────────────────┘
         │                            │
         │ depends on                 │ depends on
         │                            │
         ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────────┐
│  vscode-outliner-      │   │  doctk-language-server         │
│  extension             │   │                                │
│  - Tree Provider       │   │  - DSL Parser                  │
│  - PythonBridge client │   │  - Completion Provider         │
│  - Operation Handler   │   │  - Hover Provider              │
│  - Drag & Drop         │   │  - AI Agent Support            │
└────────────────────────┘   └────────────────────────────────┘
```

## Critical Dependencies

### 1. doctk-core-integration (MUST BE FIRST)

**Why it must be first:**

- Provides `StructureOperations` class that both other specs depend on
- Provides `ExtensionBridge` (JSON-RPC server) that VS Code extension needs
- Provides `OperationRegistry` that Language Server needs
- Contains the fundamental document manipulation API

**Completed tasks (already done):**

- ✅ Task 1: Project structure
- ✅ Task 2: StructureOperations (promote, demote, move, nest, unnest)
- ✅ Task 3: ExtensionBridge and PythonBridge

**Critical remaining tasks:**

- ✅ Task 4: Granular document edits (CRITICAL - needed by VS Code extension) - COMPLETED
- ⚠️ Task 5: Centralized node ID generation (MEDIUM - needed by VS Code extension)

### 2. VS Code Extension & Language Server (CAN BE PARALLEL)

After core integration tasks 1-5 are complete, these two specs can be developed **in parallel**:

#### vscode-outliner-extension

**Dependencies:**

- Requires `ExtensionBridge` from core-integration (Task 3) ✅ DONE
- Requires `StructureOperations` from core-integration (Task 2) ✅ DONE
- Requires granular edits from core-integration (Task 4) ⚠️ PENDING
- Requires centralized node IDs from core-integration (Task 5) ⚠️ PENDING

**Can start after:** Core integration Tasks 1-5 complete

#### doctk-language-server

**Dependencies:**

- Requires `OperationRegistry` concept from core-integration (can implement independently)
- Requires doctk core API (external dependency)
- Does NOT require ExtensionBridge
- Does NOT require VS Code extension

**Can start after:** Core integration Tasks 1-2 complete (for understanding operations)

**Note:** Language Server can actually start earlier than VS Code extension because it has fewer dependencies.

## Recommended Implementation Order

### Phase 1: Core Integration Foundation (SEQUENTIAL)

**Must complete in order:**

1. ✅ **DONE**: Core integration Tasks 1-3

   - Project structure
   - StructureOperations
   - ExtensionBridge

1. ✅ **COMPLETED**: Core integration Task 4 (Granular edits - CRITICAL)

   - Implemented ModifiedRange dataclass
   - Implemented DiffComputer for computing granular text ranges
   - Updated all operations to return modified ranges
   - Added 16 comprehensive tests
   - Fixed bug where node IDs change after level modifications
   - All tests pass (127/127)

1. ⚠️ **NEXT**: Core integration Task 5 (Centralized node IDs - MEDIUM)

   - Required by VS Code extension for consistency
   - Blocks VS Code extension Task 9

### Phase 2: Parallel Development (PARALLEL)

After Phase 1 is complete, these can proceed **in parallel**:

#### Track A: VS Code Extension

- Task 3: Context menu operations
- Task 4: Drag-and-drop
- Task 5: Inline editing
- Task 6: Keyboard shortcuts
- Task 7: Document synchronization
- Task 8: Granular edits integration (depends on Core Task 4)
- Task 9: Centralized ID integration (depends on Core Task 5)
- Task 10: Configuration
- Task 11: Performance optimizations

#### Track B: Language Server

- Task 1: Language server foundation
- Task 2: Operation registry
- Task 3: Completion provider
- Task 4: Hover provider
- Task 5: AI agent support
- Task 6: Connect to VS Code (depends on VS Code extension existing)
- Task 7: Error recovery
- Task 8: Memory management
- Task 9: Configuration

#### Track C: Core Integration (continued)

- Task 6: REPL
- Task 7: Script execution
- Task 8: Code block execution
- Task 9: Pluggable architecture
- Task 10: Performance optimizations
- Task 11: Error recovery
- Task 12: Security features
- Task 13: Integration verification

### Phase 3: Integration & Testing (SEQUENTIAL)

After Phase 2 tracks complete:

1. Language Server Task 6: Connect to VS Code extension
1. VS Code extension Task 13: E2E testing
1. Language Server Task 11: E2E testing
1. Core integration Task 14: E2E testing
1. All specs Task N: Final polish and documentation

## Conservative Parallelization Strategy

### What CAN be done in parallel:

✅ **After Core Tasks 1-5 complete:**

- VS Code extension Tasks 3-7, 10-11 (UI features)
- Language Server Tasks 1-5, 7-9 (LSP features)
- Core integration Tasks 6-13 (execution features)

### What CANNOT be done in parallel:

❌ **Must be sequential:**

- Core integration Tasks 1-5 must complete BEFORE starting VS Code extension
- Core integration Task 4 must complete BEFORE VS Code extension Task 8
- Core integration Task 5 must complete BEFORE VS Code extension Task 9
- VS Code extension must exist BEFORE Language Server Task 6 (connection)
- All individual spec tasks must complete BEFORE their respective E2E testing

## Current Status

Based on the task files:

- ✅ **Core Integration**: Tasks 1-4 complete (foundation ready, granular edits implemented)
- ⚠️ **Core Integration**: Task 5 MEDIUM priority for VS Code extension
- ✅ **VS Code Extension**: Tasks 1-2 complete (tree provider ready)
- ⏸️ **VS Code Extension**: Partially unblocked - can implement most features, Task 5 needed for full functionality
- ⏸️ **Language Server**: Can start now (minimal dependencies)

## Recommendation

**Immediate next steps:**

1. **Complete Core Integration Task 5** (Centralized node IDs) - MEDIUM
1. **Then start parallel development:**
   - VS Code extension Tasks 3-11 (most can start now, Task 9 needs Core Task 5)
   - Language Server Tasks 1-9 (can start now)
   - Core integration Tasks 6-13 (can start now)

**Recent Progress:**

- ✅ **2025-11-18**: Completed Core Integration Task 4 (Granular edits)
  - Implemented ModifiedRange dataclass in protocols.py
  - Implemented DiffComputer class in operations.py
  - Updated all 6 operations (promote, demote, move_up, move_down, nest, unnest) to compute and return modified ranges
  - Added 16 comprehensive tests for granular edit functionality
  - Fixed critical bug where node IDs change after level modifications
  - All 127 tests pass
  - Ruff linting passes

This conservative approach ensures no rework and maintains architectural integrity.
