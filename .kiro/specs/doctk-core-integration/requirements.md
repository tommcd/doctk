# Requirements Document: doctk Core Integration & Execution

## Introduction

This document specifies the requirements for the core integration layer and execution capabilities of the doctk system. This includes the pluggable architecture that bridges UI components with the doctk core API, script execution capabilities (REPL, file execution, code blocks), performance optimization for large documents, and integration with the doctk core API.

## Glossary

- **doctk**: Document toolkit - a composable, functional toolkit for structured document manipulation
- **DSL**: Domain-Specific Language - the doctk operation syntax (e.g., `select heading | where level=2 | promote`)
- **UDAST**: Universal Document AST - the internal representation of documents in doctk
- **Operation**: A transformation function in doctk (e.g., promote, demote, nest, unnest)
- **REPL**: Read-Eval-Print Loop - an interactive command-line interface

## Requirements

### Requirement 12: DSL Execution in Terminal REPL

**User Story:** As a user experimenting with document transformations, I want to run doctk commands interactively in a terminal, so that I can test operations quickly without writing script files.

#### Acceptance Criteria

1. WHEN a user starts the doctk REPL, THE System SHALL display a prompt accepting DSL commands
1. WHEN a user enters a valid DSL command, THE REPL SHALL execute the command and display the result
1. WHEN a user enters an invalid command, THE REPL SHALL display an error message with details
1. WHEN a document is loaded in the REPL, THE REPL SHALL maintain the document state across multiple commands
1. WHEN a user exits the REPL, THE System SHALL optionally save changes to the document

### Requirement 13: Script File Execution

**User Story:** As a documentation engineer, I want to write doctk transformation scripts in `.tk` files and execute them, so that I can automate repetitive document processing tasks.

#### Acceptance Criteria

1. WHEN a `.tk` file contains valid DSL code, THE System SHALL execute the script and apply transformations to the target document
1. WHEN a script file is executed, THE System SHALL report progress and completion status
1. WHEN a script encounters an error, THE System SHALL report the error with file location and line number
1. WHEN a script completes successfully, THE System SHALL save the transformed document
1. WHEN a script is executed from VS Code, THE Extension SHALL display output in the integrated terminal

### Requirement 14: Code Block Execution in Markdown

**User Story:** As a technical writer, I want to embed doctk scripts in Markdown code blocks and execute them, so that I can document transformations alongside their implementation.

#### Acceptance Criteria

1. WHEN a Markdown document contains a code block with language identifier `doctk`, THE Extension SHALL recognize it as executable
1. WHEN a user triggers execution on a doctk code block, THE Extension SHALL execute the DSL commands
1. WHEN execution completes, THE Extension SHALL update the document with the transformation results
1. WHEN execution fails, THE Extension SHALL display error messages in the output panel
1. WHEN multiple code blocks exist, THE Extension SHALL execute only the selected code block

### Requirement 15: Pluggable Interface Architecture

**User Story:** As a platform developer, I want the outliner and LSP to use a pluggable architecture, so that I can add support for JupyterLab and other interfaces in the future without rewriting core logic.

#### Acceptance Criteria

1. WHEN the outliner is implemented, THE System SHALL separate UI logic from document manipulation logic
1. WHEN the LSP server is implemented, THE System SHALL use a platform-agnostic communication protocol
1. WHEN a new interface is added, THE System SHALL reuse the core document manipulation API
1. WHEN a new interface is added, THE System SHALL reuse the LSP server without modification
1. WHEN the architecture is reviewed, THE System SHALL demonstrate clear separation between interface and core layers

### Requirement 17: Performance for Large Documents

**User Story:** As a user working with large technical documents, I want the system to remain responsive, so that I can work efficiently regardless of document size.

#### Acceptance Criteria

1. WHEN a document contains up to 1000 headings, THE System SHALL render the tree view within 1 second
1. WHEN a document contains up to 1000 headings, THE System SHALL respond to user interactions within 200 milliseconds
1. WHEN the Language Server processes a large document, THE Language Server SHALL provide completions within 500 milliseconds
1. WHEN structural operations are performed on large documents, THE System SHALL complete operations within 2 seconds
1. WHEN memory usage exceeds 500MB, THE System SHALL implement optimization strategies to reduce memory consumption

### Requirement 20: Integration with doctk Core API

**User Story:** As a system architect, I want the outliner and LSP to use the existing doctk core API, so that all document operations are consistent and maintainable.

#### Acceptance Criteria

1. WHEN the Outliner performs a structural operation, THE Extension SHALL invoke the corresponding doctk API operation
1. WHEN the Language Server validates syntax, THE Language Server SHALL use doctk operation definitions
1. WHEN document transformations are applied, THE System SHALL use the doctk Document and Node abstractions
1. WHEN new operations are added to doctk core, THE System SHALL automatically support them in the LSP and outliner
1. WHEN the doctk API changes, THE System SHALL maintain backward compatibility or provide migration paths
