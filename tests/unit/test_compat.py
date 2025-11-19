"""Tests for backward compatibility handling."""

import importlib.metadata
from unittest.mock import patch

import pytest

from doctk.integration.compat import (
    CompatibilityChecker,
    VersionInfo,
    check_compatibility,
    check_feature,
    get_compatibility_checker,
    get_doctk_version,
)


class TestVersionInfo:
    """Test VersionInfo class."""

    def test_version_from_string(self):
        """Test parsing version from string."""
        version = VersionInfo.from_string("0.1.0")

        assert version.major == 0
        assert version.minor == 1
        assert version.patch == 0
        assert version.raw == "0.1.0"

    def test_version_from_string_with_suffix(self):
        """Test parsing version with alpha/dev suffix."""
        version = VersionInfo.from_string("0.2.0-alpha")

        assert version.major == 0
        assert version.minor == 2
        assert version.patch == 0
        assert version.raw == "0.2.0-alpha"

    def test_version_from_string_pep440_rc(self):
        """Test parsing PEP 440 release candidate version."""
        version = VersionInfo.from_string("0.2.0rc1")

        assert version.major == 0
        assert version.minor == 2
        assert version.patch == 0
        assert version.raw == "0.2.0rc1"

    def test_version_from_string_pep440_dev(self):
        """Test parsing PEP 440 dev version."""
        version = VersionInfo.from_string("0.1.dev0")

        assert version.major == 0
        assert version.minor == 1
        assert version.patch == 0
        assert version.raw == "0.1.dev0"

    def test_version_from_string_pep440_alpha(self):
        """Test parsing PEP 440 alpha version."""
        version = VersionInfo.from_string("1.0.0a1")

        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.raw == "1.0.0a1"

    def test_version_from_string_pep440_beta(self):
        """Test parsing PEP 440 beta version."""
        version = VersionInfo.from_string("1.0.0b2")

        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.raw == "1.0.0b2"

    def test_version_from_string_with_build(self):
        """Test parsing version with build metadata."""
        version = VersionInfo.from_string("1.0.0+build.123")

        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_version_from_string_no_patch(self):
        """Test parsing version without patch number."""
        version = VersionInfo.from_string("1.2")

        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 0

    def test_version_from_string_invalid(self):
        """Test parsing invalid version string."""
        with pytest.raises(ValueError, match="Invalid version string"):
            VersionInfo.from_string("invalid")

    def test_version_str(self):
        """Test version string representation."""
        version = VersionInfo(0, 1, 2, "0.1.2")

        assert str(version) == "0.1.2"

    def test_version_str_preserves_raw(self):
        """Test that __str__ preserves original version format."""
        version = VersionInfo.from_string("0.2.0-alpha")

        # Should return raw format, not reconstructed
        assert str(version) == "0.2.0-alpha"

        version_rc = VersionInfo.from_string("1.0.0rc1")
        assert str(version_rc) == "1.0.0rc1"

    def test_version_comparison_less_than(self):
        """Test version comparison (less than)."""
        v1 = VersionInfo(0, 1, 0, "0.1.0")
        v2 = VersionInfo(0, 2, 0, "0.2.0")

        assert v1 < v2
        assert v1 <= v2
        assert not v1 > v2
        assert not v1 >= v2

    def test_version_comparison_greater_than(self):
        """Test version comparison (greater than)."""
        v1 = VersionInfo(1, 0, 0, "1.0.0")
        v2 = VersionInfo(0, 2, 0, "0.2.0")

        assert v1 > v2
        assert v1 >= v2
        assert not v1 < v2
        assert not v1 <= v2

    def test_version_comparison_equal(self):
        """Test version comparison (equal)."""
        v1 = VersionInfo(1, 0, 0, "1.0.0")
        v2 = VersionInfo(1, 0, 0, "1.0.0")

        assert v1 == v2
        assert v1 <= v2
        assert v1 >= v2
        assert not v1 < v2
        assert not v1 > v2

    def test_version_comparison_patch_level(self):
        """Test version comparison at patch level."""
        v1 = VersionInfo(1, 0, 1, "1.0.1")
        v2 = VersionInfo(1, 0, 2, "1.0.2")

        assert v1 < v2
        assert v1 <= v2


class TestCompatibilityChecker:
    """Test CompatibilityChecker class."""

    def test_checker_initialization(self):
        """Test that checker initializes correctly."""
        checker = CompatibilityChecker()

        assert checker.doctk_version is not None
        assert isinstance(checker.doctk_version, VersionInfo)

    def test_checker_gets_version(self):
        """Test that checker gets doctk version."""
        checker = CompatibilityChecker()

        # Should get the actual doctk version
        version = checker.get_version()
        assert isinstance(version, VersionInfo)
        assert version.major >= 0

    def test_checker_compatibility_check(self):
        """Test that checker can check compatibility."""
        checker = CompatibilityChecker()

        # Current version should be compatible
        assert checker.is_compatible() is True

    def test_checker_feature_check_available(self):
        """Test feature check for available feature."""
        checker = CompatibilityChecker()

        # Feature requiring version 0.1.0 should be available
        available = checker.check_feature("basic_operations", "0.1.0")
        assert available is True

    def test_checker_feature_check_unavailable(self):
        """Test feature check for unavailable feature."""
        checker = CompatibilityChecker()

        # Feature requiring a very high version should not be available
        available = checker.check_feature("future_feature", "99.0.0")
        assert available is False

    @patch("doctk.integration.compat.importlib.metadata.version")
    def test_checker_handles_old_version(self, mock_version):
        """Test checker warns about old version."""
        # Simulate old doctk version
        mock_version.return_value = "0.0.1"

        checker = CompatibilityChecker()

        # Should still initialize but might log warning
        assert checker.doctk_version.major == 0
        assert checker.doctk_version.minor == 0
        assert checker.doctk_version.patch == 1

    @patch("doctk.integration.compat.importlib.metadata.version")
    def test_checker_handles_package_not_found(self, mock_version):
        """Test checker handles missing doctk package."""
        mock_version.side_effect = importlib.metadata.PackageNotFoundError("doctk")

        with pytest.raises(ImportError, match="doctk package not found"):
            CompatibilityChecker()


class TestGlobalAPI:
    """Test global API functions."""

    def test_get_compatibility_checker_singleton(self):
        """Test that get_compatibility_checker returns singleton."""
        checker1 = get_compatibility_checker()
        checker2 = get_compatibility_checker()

        # Should be the same instance
        assert checker1 is checker2

    def test_check_compatibility(self):
        """Test check_compatibility function."""
        result = check_compatibility()

        assert isinstance(result, bool)
        assert result is True  # Current version should be compatible

    def test_get_doctk_version(self):
        """Test get_doctk_version function."""
        version = get_doctk_version()

        assert isinstance(version, VersionInfo)
        assert version.major >= 0

    def test_check_feature(self):
        """Test check_feature function."""
        # Feature requiring version 0.1.0 should be available
        available = check_feature("basic_operations", "0.1.0")
        assert available is True

        # Feature requiring future version should not be available
        unavailable = check_feature("future_feature", "99.0.0")
        assert unavailable is False


class TestVersionComparisons:
    """Test version comparison edge cases."""

    def test_version_major_comparison(self):
        """Test comparison at major version level."""
        v1 = VersionInfo(0, 9, 9, "0.9.9")
        v2 = VersionInfo(1, 0, 0, "1.0.0")

        assert v1 < v2

    def test_version_minor_comparison(self):
        """Test comparison at minor version level."""
        v1 = VersionInfo(1, 1, 9, "1.1.9")
        v2 = VersionInfo(1, 2, 0, "1.2.0")

        assert v1 < v2

    def test_version_not_equal_to_non_version(self):
        """Test version comparison with non-VersionInfo object."""
        v1 = VersionInfo(1, 0, 0, "1.0.0")

        assert v1 != "1.0.0"
        assert v1 != 1.0
        assert v1 != None  # noqa: E711

    def test_version_hash(self):
        """Test that VersionInfo is hashable."""
        v1 = VersionInfo(1, 0, 0, "1.0.0")
        v2 = VersionInfo(1, 0, 0, "1.0.0")
        v3 = VersionInfo(1, 0, 1, "1.0.1")

        # Equal versions should have equal hashes
        assert hash(v1) == hash(v2)

        # Different versions should (usually) have different hashes
        assert hash(v1) != hash(v3)

        # Should be usable in sets
        version_set = {v1, v2, v3}
        assert len(version_set) == 2  # v1 and v2 are equal

        # Should be usable as dict keys
        version_dict = {v1: "first", v2: "second", v3: "third"}
        assert len(version_dict) == 2
        assert version_dict[v1] == "second"  # v2 overwrote v1


class TestBreakingChanges:
    """Test breaking change handling."""

    def test_breaking_changes_dict_exists(self):
        """Test that BREAKING_CHANGES dict is defined."""
        assert hasattr(CompatibilityChecker, "BREAKING_CHANGES")
        assert isinstance(CompatibilityChecker.BREAKING_CHANGES, dict)

    def test_min_version_is_defined(self):
        """Test that MIN_VERSION is defined."""
        assert hasattr(CompatibilityChecker, "MIN_VERSION")
        assert isinstance(CompatibilityChecker.MIN_VERSION, VersionInfo)

    @patch("doctk.integration.compat.importlib.metadata.version")
    def test_breaking_changes_detection(self, mock_version, monkeypatch):
        """Test that breaking changes are detected and logged."""
        # Simulate version with breaking changes
        mock_version.return_value = "0.1.0"

        # Create a copy of BREAKING_CHANGES and add test data
        test_breaking_changes = {
            "0.1.0": {
                "changes": ["Test breaking change"],
                "migration": "Use new API",
            }
        }

        # Use monkeypatch for automatic cleanup after test
        monkeypatch.setattr(
            CompatibilityChecker, "BREAKING_CHANGES", test_breaking_changes
        )

        checker = CompatibilityChecker()

        # Should initialize successfully
        assert checker.is_compatible() is True


class TestIntegration:
    """Integration tests for compatibility checking."""

    def test_full_compatibility_workflow(self):
        """Test complete compatibility checking workflow."""
        # Get checker
        checker = get_compatibility_checker()

        # Check version
        version = checker.get_version()
        assert version.major >= 0

        # Check compatibility
        assert checker.is_compatible() is True

        # Check features
        basic_available = checker.check_feature("basic", "0.1.0")
        future_available = checker.check_feature("future", "99.0.0")

        assert basic_available is True
        assert future_available is False

    def test_import_from_lsp_module(self):
        """Test that compatibility functions are exported from lsp module."""
        from doctk import lsp

        assert hasattr(lsp, "check_compatibility")
        assert hasattr(lsp, "get_doctk_version")
        assert hasattr(lsp, "check_feature")
        assert hasattr(lsp, "CompatibilityChecker")
        assert hasattr(lsp, "VersionInfo")
