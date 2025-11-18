# Requirements Document: doctk Language Server

## Introduction

This document specifies the requirements for a Language Server Protocol (LSP) implementation for the doctk DSL (Domain-Specific Language). The language server provides intelligent code completion, validation, and documentation for doctk transformation scripts, enabling both human users and AI agents to effectively work with the doctk DSL.

The language server follows the LSP standard, ensuring compatibility with multiple editors and providing a well-tested communication layer. It offers real-time syntax validation, context-aware auto-completion, hover documentation, and structured information exposure for AI consumption.

## Glossary

- **doctk**: Document toolkit - a composable, functional toolkit for structured document manipulation
- **DSL**: Domain-Specific Language - the doctk operation syntax (e.g., `select heading | where level=2 | promote`)
- **LSP**: Language Server Protocol - a protocol for providing language intelligence features
- **Language Client**: The editor extension component that communicates with the language server
- **Language Server**: The backend process that provides language intelligence features
- **Operation**: A transformation function in doctk (e.g., promote, demote, nest, unnest)
- **Diagnostic**: An error, warning, or information message about code

## Requirements

### Requirement 7: Language Server for DSL

**User Story:** As a developer, I want a language server that understands the doctk DSL, so that I can write transformation scripts with intelligent code completion and validation.

#### Acceptance Criteria

1. WHEN a `.tk` file is opened in VS Code, THE Language Server SHALL activate and provide language features
1. WHEN doctk DSL code is present in a Markdown code block with language identifier `doctk`, THE Language Server SHALL provide language features
1. WHEN the Language Server starts, THE Language Server SHALL initialize within 2 seconds
1. WHEN the Language Server encounters an error, THE Language Server SHALL log diagnostic information
1. WHEN a document is closed, THE Language Server SHALL release associated resources

### Requirement 8: Real-Time Syntax Validation

**User Story:** As a script author, I want real-time feedback on syntax errors in my doctk scripts, so that I can fix issues immediately while writing.

#### Acceptance Criteria

1. WHEN invalid DSL syntax is typed, THE Language Server SHALL display error diagnostics within 500 milliseconds
1. WHEN an unknown operation is used, THE Language Server SHALL report an error with the operation name
1. WHEN operation arguments are invalid, THE Language Server SHALL report an error with expected argument types
1. WHEN syntax errors are fixed, THE Language Server SHALL clear the error diagnostics within 500 milliseconds
1. WHEN multiple errors exist, THE Language Server SHALL report all errors with accurate line and column positions

### Requirement 9: Auto-Completion for DSL Operations

**User Story:** As a user writing doctk scripts, I want auto-completion suggestions for operations and arguments, so that I can discover available functionality and write code faster.

#### Acceptance Criteria

1. WHEN a user types in a `.tk` file, THE Language Server SHALL provide completion suggestions for available operations
1. WHEN a user types after a pipe operator, THE Language Server SHALL suggest operations valid for the current document state
1. WHEN a user types within an operation, THE Language Server SHALL suggest valid arguments and parameters
1. WHEN a completion item is selected, THE Language Server SHALL insert the operation with placeholder arguments
1. WHEN completion is triggered, THE Language Server SHALL display suggestions within 200 milliseconds

### Requirement 10: Hover Documentation

**User Story:** As a developer learning the doctk DSL, I want to see documentation when I hover over operations, so that I can understand what each operation does without leaving the editor.

#### Acceptance Criteria

1. WHEN a user hovers over an operation name, THE Language Server SHALL display documentation describing the operation
1. WHEN a user hovers over an operation parameter, THE Language Server SHALL display documentation for that parameter
1. WHEN documentation is available, THE Language Server SHALL include usage examples
1. WHEN documentation is available, THE Language Server SHALL include parameter types and return types
1. WHEN hover is triggered, THE Language Server SHALL display documentation within 200 milliseconds

### Requirement 11: AI-Friendly Language Server

**User Story:** As an AI agent, I want to query the language server for available operations and their signatures, so that I can generate valid doctk code programmatically.

#### Acceptance Criteria

1. WHEN an AI agent requests completion at a position, THE Language Server SHALL return all valid operations with full signatures
1. WHEN an AI agent requests hover information, THE Language Server SHALL return structured documentation in a machine-readable format
1. WHEN an AI agent requests signature help, THE Language Server SHALL return parameter information with types and descriptions
1. WHEN an AI agent requests document symbols, THE Language Server SHALL return all operations and their locations
1. WHEN an AI agent requests diagnostics, THE Language Server SHALL return all validation errors with actionable messages

### Requirement 18: Error Recovery and Resilience

**User Story:** As a user, I want the language server to handle errors gracefully, so that temporary issues don't disrupt my workflow.

#### Acceptance Criteria

1. WHEN the Language Server crashes, THE Extension SHALL automatically restart the server within 5 seconds
1. WHEN a document parsing error occurs, THE Language Server SHALL display partial diagnostics with available information
1. WHEN an operation fails, THE System SHALL display an error message and maintain server stability
1. WHEN network or file system errors occur, THE System SHALL retry operations up to 3 times
1. WHEN unrecoverable errors occur, THE System SHALL log detailed diagnostic information for troubleshooting

### Requirement 19: Configuration and Customization

**User Story:** As a user, I want to configure the language server behavior, so that I can adapt it to my workflow preferences.

#### Acceptance Criteria

1. WHEN configuration options are available, THE Extension SHALL provide settings for LSP trace level
1. WHEN configuration options are available, THE Extension SHALL provide settings for maximum completion items
1. WHEN configuration options are available, THE Extension SHALL provide settings to enable/disable the language server
1. WHEN settings are changed, THE Extension SHALL apply changes without requiring a restart
1. WHEN invalid settings are provided, THE Extension SHALL use default values and display a warning
