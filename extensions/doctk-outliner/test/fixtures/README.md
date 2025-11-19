# Performance Test Fixtures

This directory contains test documents for verifying the VSCode outliner extension's performance with large documents.

## Test Documents

### `large_document.md` (1500 headings)
- **Purpose**: Test performance with documents exceeding the large document threshold
- **Total headings**: 1500 (1 title + 1499 generated headings)
- **Expected Behavior**:
  - Tree nodes should start in **Collapsed** state (lazy loading enabled)
  - Initial tree rendering should complete within 500ms
  - Expanding nodes should be responsive (<100ms)
  - No UI freezing or lag during interactions

### `threshold_test.md` (999 headings)
- **Purpose**: Test behavior just below the large document threshold (default: 1000)
- **Total headings**: 999 (1 title + 998 generated headings)
- **Expected Behavior**:
  - Tree nodes should start in **Expanded** state (normal behavior)
  - All nodes visible immediately
  - Responsive UI interactions

## Manual Testing Procedure

1. **Install the extension**:
   ```bash
   cd /home/user/doctk/extensions/doctk-outliner
   npm install
   npm run compile
   ```

2. **Open test document in VS Code**:
   - Open `large_document.md` or `threshold_test.md` in VS Code
   - The doctk outliner view should appear in the Explorer sidebar

3. **Verify performance**:
   - Initial tree rendering should be fast (<500ms)
   - Tree should be responsive during scrolling
   - Expanding/collapsing nodes should be instant
   - No visible lag or freezing

4. **Verify lazy loading** (for large_document.md):
   - Check that nodes start collapsed (configuration: `doctk.performance.enableLazyLoading: true`)
   - Expanding a node should load its children instantly
   - Tree should remain responsive with all nodes expanded

5. **Verify operations**:
   - Test promote/demote operations on various nodes
   - Test move up/down operations
   - Test drag-and-drop nesting
   - All operations should complete within 500ms

## Configuration

The performance behavior is controlled by these VS Code settings:

- `doctk.performance.largeDocumentThreshold`: Number of headings to trigger optimizations (default: 1000)
- `doctk.performance.enableLazyLoading`: Enable lazy loading for large documents (default: true)

To test different thresholds, adjust these settings in VS Code:
```json
{
  "doctk.performance.largeDocumentThreshold": 500,
  "doctk.performance.enableLazyLoading": true
}
```

## Regenerating Test Documents

Use the `generate_large_doc.py` script to create custom test documents:

```bash
# Generate document with specific number of headings
python3 generate_large_doc.py --headings 2000 --output custom_test.md

# Generate document with 10,000 headings (stress test)
python3 generate_large_doc.py --headings 10000 --output stress_test.md
```

## Automated E2E Tests

Automated end-to-end tests will be implemented in Task 13. These tests will:
- Programmatically open test documents
- Measure tree rendering time
- Verify lazy loading behavior
- Benchmark operation performance
- Validate response time requirements (<500ms)

For now, use the manual testing procedure above to verify performance.

## Performance Requirements

From the design specification:
- **Tree rendering**: <500ms for initial display
- **Operations**: <500ms for all structural operations
- **UI responsiveness**: No visible lag or freezing
- **Large documents**: Support for 1000+ headings without performance degradation
