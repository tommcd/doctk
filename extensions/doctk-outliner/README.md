# doctk Document Outliner

A VS Code extension that provides a tree-based document outliner for Markdown files with interactive structure manipulation through drag-and-drop operations, context menus, and keyboard shortcuts.

## Features

### 📋 Tree-Based Document Outliner

View your Markdown document structure as a hierarchical tree in the VS Code sidebar:

- **Automatic Structure Detection**: Automatically parses Markdown headings and displays them as a tree
- **Real-Time Synchronization**: Tree updates automatically when you edit the document
- **Click to Navigate**: Click any node to jump to that section in your document
- **Visual Hierarchy**: See the complete document structure at a glance

### 🎯 Context Menu Operations

Right-click on any section in the outliner to:

- **Promote** (`Ctrl+Shift+Up` / `Cmd+Shift+Up`): Decrease heading level (e.g., h3 → h2)
- **Demote** (`Ctrl+Shift+Down` / `Cmd+Shift+Down`): Increase heading level (e.g., h2 → h3)
- **Move Up** (`Alt+Up`): Move section up in sibling order
- **Move Down** (`Alt+Down`): Move section down in sibling order
- **Rename** (`F2`): Edit heading text inline
- **Delete** (`Delete`): Remove section from document

All operations update both the tree view and the Markdown document, with full undo/redo support.

### 🖱️ Drag-and-Drop Support

Reorganize your document structure intuitively:

- **Drag nodes** to change document hierarchy
- **Drop onto a node** to nest the section under it
- **Drop at root level** to unnest the section
- **Visual feedback** shows valid drop targets
- **Invalid drops prevented** (e.g., cannot drop node onto its own descendant)

**Note**: Due to VS Code API limitations, precise sibling reordering via drag-and-drop is not supported. Use **Move Up** and **Move Down** context menu operations for precise positioning within sibling lists.

### ⌨️ Keyboard Shortcuts

Navigate and manipulate your document structure without touching the mouse:

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Promote Section | `Ctrl+Shift+Up` | `Cmd+Shift+Up` |
| Demote Section | `Ctrl+Shift+Down` | `Cmd+Shift+Down` |
| Move Section Up | `Alt+Up` | `Alt+Up` |
| Move Section Down | `Alt+Down` | `Alt+Down` |
| Rename Section | `F2` | `F2` |
| Delete Section | `Delete` | `Delete` |

All shortcuts are customizable through VS Code's Keyboard Shortcuts settings.

### ⏪ Undo/Redo Support

All structural changes made through the outliner are fully integrated with VS Code's undo/redo system:

- Press `Ctrl+Z` / `Cmd+Z` to undo changes
- Press `Ctrl+Shift+Z` / `Cmd+Shift+Z` to redo changes
- Complete undo history maintained across save operations

### 🔄 Document Synchronization

Bidirectional synchronization ensures consistency:

- **Editor → Tree**: Changes in the Markdown editor update the tree view within 500ms
- **Tree → Editor**: Changes in the tree view update the Markdown content immediately
- **External Changes**: Detects and handles external file modifications
- **Debounced Updates**: Rapid changes are batched to prevent performance issues

## Requirements

- **VS Code**: Version 1.80.0 or higher
- **Python**: Python 3.12 or higher (for doctk backend)
- **doctk**: The doctk Python package must be installed

### Installing doctk

The extension requires the doctk Python package to be installed:

```bash
# Using pip
pip install doctk

# Using uv (recommended)
uv pip install doctk
```

Alternatively, if you're developing doctk locally:

```bash
# Install from source
cd /path/to/doctk
uv pip install -e .
```

## Installation

### From .vsix File

1. Download the latest `.vsix` file from the releases page
2. Open VS Code
3. Go to Extensions view (`Ctrl+Shift+X` / `Cmd+Shift+X`)
4. Click the "..." menu at the top right
5. Select "Install from VSIX..."
6. Choose the downloaded `.vsix` file

### From Source

```bash
# Clone the repository
git clone https://github.com/tommcd/doctk.git
cd doctk/extensions/doctk-outliner

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Package extension
npx @vscode/vsce package

# Install the generated .vsix file in VS Code
```

## Usage

### Opening the Outliner

1. Open a Markdown (`.md`) file in VS Code
2. The "Document Outline" view appears automatically in the Explorer sidebar
3. If not visible, open it via: **View → Open View → Document Outline**

### Basic Operations

#### Navigate to Section

- **Click** any node in the tree to jump to that section in the editor

#### Promote/Demote Headings

- **Right-click** a node → Select "Promote Section" or "Demote Section"
- Or use keyboard shortcuts: `Ctrl+Shift+Up` / `Ctrl+Shift+Down`

#### Reorder Sections

- **Right-click** a node → Select "Move Section Up" or "Move Section Down"
- Or use keyboard shortcuts: `Alt+Up` / `Alt+Down`

#### Rename Section

- **Right-click** a node → Select "Rename Section"
- Or press `F2` when a node is selected
- Type new heading text in the input box and press Enter

#### Delete Section

- **Right-click** a node → Select "Delete Section"
- Or press `Delete` when a node is selected
- Confirmation is not required (use undo if needed)

#### Change Hierarchy via Drag-and-Drop

- **Drag** a node to move it
- **Drop onto another node** to nest it as a child
- **Drop at root** (bottom of tree) to unnest it to top level

### Refreshing the Outline

The outline refreshes automatically when the document changes. To force a manual refresh:

- Click the **Refresh** icon in the outline view toolbar
- Or run command: **doctk: Refresh Outline**

## Configuration

Configure the extension through VS Code settings (**File → Preferences → Settings** or `Ctrl+,`):

### Outliner Settings

```json
{
  // Automatically refresh the outline when the document changes
  "doctk.outliner.autoRefresh": true,

  // Delay in milliseconds before refreshing the outline (debouncing)
  "doctk.outliner.refreshDelay": 300,

  // Show a preview of content in the outline (experimental)
  "doctk.outliner.showContentPreview": false,

  // Maximum length of content preview
  "doctk.outliner.maxPreviewLength": 50
}
```

### Language Server Settings

```json
{
  // Enable the doctk language server for .tk files
  "doctk.lsp.enabled": true,

  // Trace LSP communication for debugging
  "doctk.lsp.trace": "off", // Options: "off", "messages", "verbose"

  // Maximum number of completion items to show
  "doctk.lsp.maxCompletionItems": 50,

  // Python command or path to Python executable
  "doctk.lsp.pythonCommand": "python3" // or "python", or "/path/to/python"
}
```

### Performance Settings

```json
{
  // Number of headings to consider a document 'large'
  "doctk.performance.largeDocumentThreshold": 1000,

  // Enable virtualization for large documents (future feature)
  "doctk.performance.enableVirtualization": true
}
```

### Customizing Keyboard Shortcuts

To customize keyboard shortcuts:

1. Open **File → Preferences → Keyboard Shortcuts** (`Ctrl+K Ctrl+S`)
2. Search for "doctk"
3. Click the pencil icon next to any command to change its keybinding

## Known Limitations

### Drag-and-Drop Position Detection

Due to VS Code's `TreeDragAndDropController` API limitations, the extension **cannot detect drop position** (before/after a node). This means:

- ✅ **Supported**: Drag-and-drop to change hierarchy (nest/unnest)
- ❌ **Not Supported**: Precise sibling reordering via drag-and-drop

**Workaround**: Use the **Move Up** and **Move Down** context menu operations for precise positioning within sibling lists. This provides equivalent functionality with better reliability.

### Large Document Performance

For documents with over 1000 headings, some operations may take longer than 500ms. Performance optimizations (virtual scrolling, lazy loading) are planned for future releases.

## Troubleshooting

### "Python bridge failed to start"

**Cause**: The Python backend process couldn't be started.

**Solutions**:
- Verify Python 3.12+ is installed: `python3 --version`
- Verify doctk is installed: `python3 -c "import doctk; print(doctk.__version__)"`
- Check the `doctk.lsp.pythonCommand` setting points to the correct Python executable
- Check the Output panel (**View → Output**) and select "doctk" for detailed logs

### Outline not updating

**Cause**: Auto-refresh might be disabled or debouncing delay is too high.

**Solutions**:
- Check `doctk.outliner.autoRefresh` is `true`
- Reduce `doctk.outliner.refreshDelay` to a lower value (e.g., 100ms)
- Click the Refresh icon in the outline view toolbar

### Operations not working

**Cause**: The Python backend might not be responding.

**Solutions**:
- Check the Output panel for error messages
- Restart VS Code
- Reinstall the doctk Python package: `pip install --upgrade --force-reinstall doctk`

### Extension not activating

**Cause**: The extension only activates for Markdown files.

**Solutions**:
- Ensure you're editing a `.md` file
- Check the file language mode is set to "Markdown"
- Manually activate via command: **doctk: Refresh Outline**

## Development

### Building from Source

```bash
# Clone repository
git clone https://github.com/tommcd/doctk.git
cd doctk/extensions/doctk-outliner

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch mode for development
npm run watch
```

### Running Extension in Development Mode

1. Open `extensions/doctk-outliner` folder in VS Code
2. Press `F5` to launch Extension Development Host
3. Open a Markdown file to test the extension

### Running Tests

```bash
# Lint TypeScript code
npm run lint

# Run tests (when available)
npm test
```

## Contributing

Contributions are welcome! Please see the main [CONTRIBUTING.md](../../CONTRIBUTING.md) in the doctk repository for guidelines.

## Architecture

This extension is part of the larger doctk project ecosystem:

```
┌─────────────────────────────────────────────────────────────┐
│                     VS Code Extension                        │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  Outliner View   │         │   Document Sync         │  │
│  │  (Tree Provider) │◄────────┤   Manager               │  │
│  └────────┬─────────┘         └──────────┬──────────────┘  │
│           │                               │                  │
│           ▼                               ▼                  │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  Operation       │         │   Python Bridge         │  │
│  │  Handler         │────────►│   (JSON-RPC)            │  │
│  └──────────────────┘         └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                          │
                                          │ JSON-RPC
                                          ▼
                              ┌─────────────────────┐
                              │  doctk Core API     │
                              │  (Python Backend)   │
                              └─────────────────────┘
```

For detailed design documentation, see:
- [Design Document](../../.kiro/specs/vscode-outliner-extension/design.md)
- [Requirements Document](../../.kiro/specs/vscode-outliner-extension/requirements.md)
- [doctk Documentation](https://tommcd.github.io/doctk/)

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Support

- **Documentation**: [https://tommcd.github.io/doctk/](https://tommcd.github.io/doctk/)
- **Issues**: [https://github.com/tommcd/doctk/issues](https://github.com/tommcd/doctk/issues)
- **Discussions**: [https://github.com/tommcd/doctk/discussions](https://github.com/tommcd/doctk/discussions)

## Acknowledgments

Built with:
- [VS Code Extension API](https://code.visualstudio.com/api)
- [doctk](https://github.com/tommcd/doctk) - Composable functional toolkit for document manipulation
- [TypeScript](https://www.typescriptlang.org/)
