"""
Tests to verify VS Code extension can actually use the Python bridge.

These tests ensure the module paths referenced in the TypeScript extension code
actually exist and work, preventing bugs like trying to import non-existent modules.
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest

# Module path constant - matches what the VS Code extension uses
BRIDGE_MODULE_PATH = "doctk.integration.bridge"
# Old incorrect path that should NOT work
OLD_BROKEN_PATH = "doctk.lsp.bridge"


def test_bridge_module_is_importable():
    """Verify doctk.integration.bridge module can be imported.

    This is the module path the VS Code extension uses to start the Python bridge.
    If this test fails, the extension won't be able to start the backend.
    """
    # This should not raise ImportError
    import doctk.integration.bridge  # noqa: F401


def test_bridge_module_can_run_as_main():
    """Verify bridge module loads without import errors when run with python -m.

    This is how the VS Code extension actually starts the bridge process.
    If this fails, the extension will fail with "No module named" error.

    Note: We don't actually run the bridge to completion (it runs indefinitely),
    we just verify the module loads successfully without import errors.
    """
    # Start the process and immediately terminate to check for import errors
    process = subprocess.Popen(
        [sys.executable, "-m", BRIDGE_MODULE_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Use communicate() with timeout to safely check stderr
        try:
            _, stderr = process.communicate(timeout=0.5)
        except subprocess.TimeoutExpired:
            # Timeout is expected - bridge runs indefinitely
            # Kill it and get the output
            process.kill()
            _, stderr = process.communicate()

        # An ImportError would appear in stderr with "No module named"
        stderr_text = stderr.decode()
        assert "No module named" not in stderr_text, f"Module import failed: {stderr_text}"
        assert "ModuleNotFoundError" not in stderr_text, f"Module not found: {stderr_text}"

    finally:
        # Ensure cleanup
        if process.poll() is None:
            process.kill()
            process.wait()


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
    """Integration test: spawn the bridge process and wait for ready signal.

    Verifies the bridge process starts successfully without import errors
    by waiting for the BRIDGE_READY signal that the bridge emits upon
    successful startup.

    This catches runtime errors that pure import tests might miss.
    """
    # Start the bridge process
    process = subprocess.Popen(
        [sys.executable, "-m", BRIDGE_MODULE_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
    )

    try:
        # Wait for BRIDGE_READY signal (max 5 seconds)
        ready = False
        start_time = time.time()
        timeout = 5.0

        while time.time() - start_time < timeout:
            # Check if process crashed
            if process.poll() is not None:
                # Process exited - get error output
                _, stderr = process.communicate()
                pytest.fail(
                    f"Bridge process crashed immediately. "
                    f"Return code: {process.returncode}. "
                    f"Stderr: {stderr}"
                )

            # Read a line from stdout (non-blocking check)
            # Use readline() which will return when a line is available
            try:
                line = process.stdout.readline()
                if "BRIDGE_READY" in line:
                    ready = True
                    break
            except Exception:  # noqa: S110
                # If reading fails, continue waiting
                pass

            time.sleep(0.1)

        assert ready, (
            "Bridge did not emit BRIDGE_READY signal within timeout. "
            "This indicates the bridge process failed to start properly."
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
    process = subprocess.Popen(
        [sys.executable, "-m", OLD_BROKEN_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Use communicate() with timeout to safely get output
        try:
            _, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            _, stderr = process.communicate()

        stderr_text = stderr.decode()

        # This SHOULD fail with ImportError or ModuleNotFoundError
        assert process.returncode != 0, f"{OLD_BROKEN_PATH} should not exist"
        assert "No module named" in stderr_text or "ModuleNotFoundError" in stderr_text, (
            f"Should get module not found error. Got: {stderr_text}"
        )

    finally:
        # Ensure cleanup
        if process.poll() is None:
            process.kill()
            process.wait()
