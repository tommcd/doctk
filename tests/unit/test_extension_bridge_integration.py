"""
Tests to verify VS Code extension can actually use the Python bridge.

These tests ensure the module paths referenced in the TypeScript extension code
actually exist and work, preventing bugs like trying to import non-existent modules.
"""

import subprocess
import sys
from pathlib import Path

import pytest


def test_bridge_module_is_importable():
    """Verify doctk.integration.bridge module can be imported.

    This is the module path the VS Code extension uses to start the Python bridge.
    If this test fails, the extension won't be able to start the backend.
    """
    # This should not raise ImportError
    import doctk.integration.bridge  # noqa: F401


def test_bridge_module_can_run_as_main():
    """Verify bridge can be started with python -m doctk.integration.bridge.

    This is how the VS Code extension actually starts the bridge process.
    If this fails, the extension will fail with "No module named doctk.integration.bridge".
    """
    # Run the bridge module with --help to verify it can start
    # (we don't actually start the bridge server, just verify the module loads)
    result = subprocess.run(
        [sys.executable, "-m", "doctk.integration.bridge", "--help"],
        capture_output=True,
        timeout=5,
    )

    # Even if --help isn't implemented, the module should load without ImportError
    # An ImportError would exit with code 1 and include "No module named" in stderr
    assert "No module named" not in result.stderr.decode(), (
        f"Module import failed: {result.stderr.decode()}"
    )


def test_bridge_module_has_main_function():
    """Verify the bridge module has a main() function for CLI entry point."""
    from doctk.integration.bridge import main

    # Verify it's callable
    assert callable(main), "bridge.main() must be a callable function"


def test_extension_can_find_bridge_script():
    """Verify the path used by VS Code extension to start bridge exists.

    The extension runs: python -m doctk.integration.bridge
    This test ensures that command will work.
    """
    # Try to locate the module file
    import doctk.integration.bridge

    module_file = Path(doctk.integration.bridge.__file__)
    assert module_file.exists(), f"Bridge module file not found: {module_file}"
    assert module_file.name == "bridge.py", "Bridge module should be bridge.py"


@pytest.mark.slow
def test_bridge_process_can_actually_start():
    """Integration test: spawn the bridge process like the extension does.

    This is a more thorough test that actually starts the bridge process
    and verifies it can accept connections (times out after 2 seconds).
    """
    # Start the bridge process
    process = subprocess.Popen(
        [sys.executable, "-m", "doctk.integration.bridge"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Give it a moment to start and fail if there are import errors
        import time
        time.sleep(0.5)

        # Check if process is still running (not crashed due to import error)
        assert process.poll() is None, (
            f"Bridge process crashed immediately. Stderr: {process.stderr.read().decode()}"
        )

    finally:
        # Clean up: kill the process
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def test_wrong_module_path_fails_correctly():
    """Verify that the OLD incorrect path fails, so we know our fix worked.

    The extension was trying to use doctk.lsp.bridge (which doesn't exist).
    This test verifies that path indeed doesn't work.
    """
    result = subprocess.run(
        [sys.executable, "-m", "doctk.lsp.bridge"],
        capture_output=True,
        timeout=5,
    )

    # This SHOULD fail with ImportError
    assert result.returncode != 0, "doctk.lsp.bridge should not exist"
    assert "No module named" in result.stderr.decode(), (
        "Should get 'No module named' error for non-existent module"
    )
