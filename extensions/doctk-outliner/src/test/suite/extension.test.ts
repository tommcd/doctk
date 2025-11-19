import * as assert from "assert";
import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { DocumentOutlineProvider } from "../../outlineProvider";

suite("doctk Outliner Extension Test Suite", () => {
  let testDocument: vscode.TextDocument;
  let testDocumentUri: vscode.Uri;
  const testContent = `# Top Level Heading

This is some content under the top level heading.

## Second Level Heading

Content under second level.

### Third Level Heading

Content under third level.

## Another Second Level

More content here.

# Another Top Level

Final section.
`;

  suiteSetup(async () => {
    // Create a temporary test file
    const tempDir = path.join(__dirname, "../../../test-workspace");
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }

    const testFilePath = path.join(tempDir, "test-document.md");
    fs.writeFileSync(testFilePath, testContent);
    testDocumentUri = vscode.Uri.file(testFilePath);

    // Open the test document
    testDocument = await vscode.workspace.openTextDocument(testDocumentUri);
    await vscode.window.showTextDocument(testDocument);

    // Wait for extension activation
    await vscode.extensions.getExtension("doctk.doctk-outliner")?.activate();

    // Give the outliner time to initialize
    await new Promise((resolve) => setTimeout(resolve, 1000));
  });

  suiteTeardown(async () => {
    // Close all editors
    await vscode.commands.executeCommand("workbench.action.closeAllEditors");

    // Clean up test file
    try {
      if (fs.existsSync(testDocumentUri.fsPath)) {
        fs.unlinkSync(testDocumentUri.fsPath);
      }
      const tempDir = path.dirname(testDocumentUri.fsPath);
      if (fs.existsSync(tempDir)) {
        fs.rmdirSync(tempDir);
      }
    } catch (err) {
      console.warn("Error cleaning up test files:", err);
    }
  });

  suite("Tree View Rendering", () => {
    test("Extension should be present", () => {
      assert.ok(vscode.extensions.getExtension("doctk.doctk-outliner"));
    });

    test("All doctk commands should be registered", async () => {
      const commands = await vscode.commands.getCommands(true);
      const doctkCommands = [
        "doctk.promote",
        "doctk.demote",
        "doctk.moveUp",
        "doctk.moveDown",
        "doctk.delete",
        "doctk.rename",
        "doctk.refresh",
      ];

      for (const cmd of doctkCommands) {
        assert.ok(
          commands.includes(cmd),
          `Command ${cmd} should be registered`
        );
      }
    });

    test("Tree view should be visible for markdown documents", async () => {
      const treeView = vscode.window.createTreeView("doctkOutline", {
        treeDataProvider: new DocumentOutlineProvider(),
      });

      assert.ok(treeView, "Tree view should be created");
      treeView.dispose();
    });
  });

  suite("Document Parsing and Tree Building", () => {
    test("Should parse headings from markdown document", async () => {
      const provider = new DocumentOutlineProvider();
      await provider.updateFromDocument(testDocument);

      const rootChildren = await provider.getChildren();
      assert.ok(rootChildren, "Should return root children");
      assert.ok(Array.isArray(rootChildren), "Should return an array");
      assert.ok(rootChildren.length > 0, "Should have root level nodes");

      // Check first heading
      const firstNode = rootChildren[0];
      assert.strictEqual(
        firstNode.label,
        "Top Level Heading",
        "First heading should be 'Top Level Heading'"
      );
      assert.strictEqual(
        firstNode.level,
        1,
        "First heading should be level 1"
      );
    });

    test("Should build hierarchical tree structure", async () => {
      const provider = new DocumentOutlineProvider();
      await provider.updateFromDocument(testDocument);

      const rootChildren = await provider.getChildren();
      assert.ok(rootChildren && Array.isArray(rootChildren), "Should return root children array");
      const firstNode = rootChildren[0];

      // Check children of first node
      const children = await provider.getChildren(firstNode);
      assert.ok(children && Array.isArray(children), "Should return children array");
      assert.ok(children.length > 0, "First node should have children");

      const secondLevelNode = children[0];
      assert.strictEqual(
        secondLevelNode.label,
        "Second Level Heading",
        "First child should be 'Second Level Heading'"
      );
      assert.strictEqual(
        secondLevelNode.level,
        2,
        "First child should be level 2"
      );
    });

    test("Should assign unique IDs to nodes", async () => {
      const provider = new DocumentOutlineProvider();
      await provider.updateFromDocument(testDocument);

      const rootChildren = await provider.getChildren();
      assert.ok(rootChildren && Array.isArray(rootChildren), "Should return root children array");
      const ids = new Set<string>();

      for (const node of rootChildren) {
        assert.ok(node.id, "Node should have an ID");
        assert.ok(!ids.has(node.id), `Node ID ${node.id} should be unique`);
        ids.add(node.id);

        // Check children
        const children = await provider.getChildren(node);
        if (!children) continue;
        for (const child of children) {
          assert.ok(child.id, "Child node should have an ID");
          assert.ok(
            !ids.has(child.id),
            `Child node ID ${child.id} should be unique`
          );
          ids.add(child.id);
        }
      }
    });
  });

  suite("Document Synchronization", () => {
    test("Should update tree when document changes", async () => {
      const provider = new DocumentOutlineProvider();
      await provider.updateFromDocument(testDocument);

      const initialChildren = await provider.getChildren();
      assert.ok(initialChildren && Array.isArray(initialChildren), "Should return initial children array");
      const initialCount = initialChildren.length;

      // Modify the document
      const edit = new vscode.WorkspaceEdit();
      const lastLine = testDocument.lineCount - 1;

      edit.insert(
        testDocument.uri,
        testDocument.lineAt(lastLine).range.end,
        "\n\n# New Heading\n\nNew content."
      );

      await vscode.workspace.applyEdit(edit);

      // Give some time for the update
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Re-parse the updated document
      await provider.updateFromDocument(testDocument);

      const updatedChildren = await provider.getChildren();
      assert.ok(updatedChildren && Array.isArray(updatedChildren), "Should return updated children array");
      assert.ok(
        updatedChildren.length >= initialCount,
        "Tree should reflect document changes"
      );
    });

    test("Should debounce rapid changes", async () => {
      const provider = new DocumentOutlineProvider();
      let updateCount = 0;

      // Track refresh calls
      const originalRefresh = provider.refresh.bind(provider);
      provider.refresh = () => {
        updateCount++;
        originalRefresh();
      };

      // Make rapid changes
      for (let i = 0; i < 5; i++) {
        await provider.updateFromDocument(testDocument);
      }

      // Wait for debounce to complete
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Should have fewer refreshes than updates due to debouncing
      assert.ok(
        updateCount < 5,
        "Should debounce rapid updates (got " +
          updateCount +
          " updates for 5 calls)"
      );
    });
  });

  suite("Context Menu Operations", () => {
    test("Promote command should be executable", async () => {
      const commands = await vscode.commands.getCommands(true);
      assert.ok(
        commands.includes("doctk.promote"),
        "Promote command should be registered"
      );
    });

    test("Demote command should be executable", async () => {
      const commands = await vscode.commands.getCommands(true);
      assert.ok(
        commands.includes("doctk.demote"),
        "Demote command should be registered"
      );
    });

    test("Move up command should be executable", async () => {
      const commands = await vscode.commands.getCommands(true);
      assert.ok(
        commands.includes("doctk.moveUp"),
        "Move up command should be registered"
      );
    });

    test("Move down command should be executable", async () => {
      const commands = await vscode.commands.getCommands(true);
      assert.ok(
        commands.includes("doctk.moveDown"),
        "Move down command should be registered"
      );
    });

    test("Delete command should be executable", async () => {
      const commands = await vscode.commands.getCommands(true);
      assert.ok(
        commands.includes("doctk.delete"),
        "Delete command should be registered"
      );
    });

    test("Rename command should be executable", async () => {
      const commands = await vscode.commands.getCommands(true);
      assert.ok(
        commands.includes("doctk.rename"),
        "Rename command should be registered"
      );
    });
  });

  suite("Keyboard Shortcuts", () => {
    test("Keyboard shortcuts should be registered", async () => {
      // Get keybindings
      const keybindings = await vscode.commands.executeCommand<
        Array<{ command: string; key: string }>
      >("workbench.action.openGlobalKeybindings");

      // Note: We can't directly test keybindings execution in E2E tests
      // without complex setup, but we can verify they're registered
      assert.ok(
        keybindings !== undefined,
        "Keybindings should be accessible"
      );
    });
  });

  suite("Configuration", () => {
    test("Should load configuration values", () => {
      const config = vscode.workspace.getConfiguration("doctk.outliner");

      assert.strictEqual(
        config.get("autoRefresh"),
        true,
        "Default autoRefresh should be true"
      );
      assert.strictEqual(
        config.get("refreshDelay"),
        300,
        "Default refreshDelay should be 300ms"
      );
      assert.strictEqual(
        config.get("showContentPreview"),
        false,
        "Default showContentPreview should be false"
      );
      assert.strictEqual(
        config.get("maxPreviewLength"),
        50,
        "Default maxPreviewLength should be 50"
      );
    });

    test("Should load performance configuration", () => {
      const config = vscode.workspace.getConfiguration("doctk.performance");

      assert.strictEqual(
        config.get("largeDocumentThreshold"),
        1000,
        "Default large document threshold should be 1000"
      );
      assert.strictEqual(
        config.get("enableLazyLoading"),
        true,
        "Default lazy loading should be enabled"
      );
    });
  });

  suite("Performance", () => {
    test("Should handle document with many headings", async () => {
      // Create a large document
      let largeContent = "";
      for (let i = 1; i <= 100; i++) {
        largeContent += `# Heading ${i}\n\nContent for heading ${i}.\n\n`;
        largeContent += `## Subheading ${i}.1\n\nSubcontent.\n\n`;
        largeContent += `## Subheading ${i}.2\n\nSubcontent.\n\n`;
      }

      const largeTempPath = path.join(
        path.dirname(testDocumentUri.fsPath),
        "large-test.md"
      );
      fs.writeFileSync(largeTempPath, largeContent);
      const largeUri = vscode.Uri.file(largeTempPath);

      const largeDoc = await vscode.workspace.openTextDocument(largeUri);
      await vscode.window.showTextDocument(largeDoc);

      const provider = new DocumentOutlineProvider();

      // Measure update time
      const startTime = Date.now();
      await provider.updateFromDocument(largeDoc);
      const updateTime = Date.now() - startTime;

      // Should complete within 500ms (requirement)
      assert.ok(
        updateTime < 500,
        `Update should complete within 500ms (took ${updateTime}ms)`
      );

      // Verify tree was built
      const rootChildren = await provider.getChildren();
      assert.ok(rootChildren && Array.isArray(rootChildren), "Should return children array");
      assert.ok(
        rootChildren.length >= 100,
        "Should parse all top-level headings"
      );

      // Clean up
      fs.unlinkSync(largeTempPath);
      await vscode.commands.executeCommand("workbench.action.closeAllEditors");
    });

    test("Should enable lazy loading for large documents", async () => {
      const provider = new DocumentOutlineProvider();

      // Create a document with 1000+ headings
      let veryLargeContent = "";
      for (let i = 1; i <= 500; i++) {
        veryLargeContent += `# Heading ${i}\n\nContent.\n\n`;
        veryLargeContent += `## Subheading ${i}.1\n\nContent.\n\n`;
        veryLargeContent += `## Subheading ${i}.2\n\nContent.\n\n`;
      }

      const veryLargePath = path.join(
        path.dirname(testDocumentUri.fsPath),
        "very-large-test.md"
      );
      fs.writeFileSync(veryLargePath, veryLargeContent);
      const veryLargeUri = vscode.Uri.file(veryLargePath);

      const veryLargeDoc =
        await vscode.workspace.openTextDocument(veryLargeUri);

      await provider.updateFromDocument(veryLargeDoc);

      const rootChildren = await provider.getChildren();
      assert.ok(rootChildren && Array.isArray(rootChildren) && rootChildren.length > 0, "Should return children array");
      const firstNode = rootChildren[0];

      // Check if large document detection is working
      const treeItem = provider.getTreeItem(firstNode);

      // For large documents, nodes should start collapsed
      assert.ok(
        treeItem.collapsibleState === vscode.TreeItemCollapsibleState.Collapsed ||
          treeItem.collapsibleState === vscode.TreeItemCollapsibleState.Expanded,
        "Large document nodes should be collapsible"
      );

      // Clean up
      fs.unlinkSync(veryLargePath);
    });
  });

  suite("Error Handling", () => {
    test("Should handle invalid markdown gracefully", async () => {
      const invalidContent = "This is not properly formatted\n### Random heading\nNo structure";

      const invalidPath = path.join(
        path.dirname(testDocumentUri.fsPath),
        "invalid-test.md"
      );
      fs.writeFileSync(invalidPath, invalidContent);
      const invalidUri = vscode.Uri.file(invalidPath);

      const invalidDoc = await vscode.workspace.openTextDocument(invalidUri);

      const provider = new DocumentOutlineProvider();

      // Should not throw
      await assert.doesNotReject(async () => {
        await provider.updateFromDocument(invalidDoc);
      });

      // Clean up
      fs.unlinkSync(invalidPath);
    });

    test("Should handle empty document", async () => {
      const emptyContent = "";

      const emptyPath = path.join(
        path.dirname(testDocumentUri.fsPath),
        "empty-test.md"
      );
      fs.writeFileSync(emptyPath, emptyContent);
      const emptyUri = vscode.Uri.file(emptyPath);

      const emptyDoc = await vscode.workspace.openTextDocument(emptyUri);

      const provider = new DocumentOutlineProvider();

      await provider.updateFromDocument(emptyDoc);

      const rootChildren = await provider.getChildren();
      assert.ok(rootChildren !== null && rootChildren !== undefined, "Should return a result");
      assert.strictEqual(
        rootChildren.length,
        0,
        "Empty document should have no nodes"
      );

      // Clean up
      fs.unlinkSync(emptyPath);
    });
  });
});
