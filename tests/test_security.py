#!/usr/bin/env python3
"""
NeuroRift Security Test Suite
Tests security utilities, authentication, and input validation
"""

import pytest
import os
import tempfile
from pathlib import Path

from utils.security_utils import (
    SecurityValidator,
    RateLimiter,
    FilePermissionManager,
    TokenGenerator,
    validate_target,
    sanitize_filename,
)
from utils.auth import AuthManager, Role, Permission, User, Session


class TestSecurityValidator:
    """Test security validation functions"""

    def test_validate_domain_valid(self):
        """Test valid domain validation"""
        assert SecurityValidator.validate_domain("example.com")
        assert SecurityValidator.validate_domain("sub.example.com")
        assert SecurityValidator.validate_domain("test.co.uk")

    def test_validate_domain_invalid(self):
        """Test invalid domain validation"""
        assert not SecurityValidator.validate_domain("")
        assert not SecurityValidator.validate_domain("invalid domain")
        assert not SecurityValidator.validate_domain("../etc/passwd")
        assert not SecurityValidator.validate_domain(None)

    def test_validate_ip_valid(self):
        """Test valid IP validation"""
        assert SecurityValidator.validate_ip("192.168.1.1")
        assert SecurityValidator.validate_ip("10.0.0.1")
        assert SecurityValidator.validate_ip("8.8.8.8")

    def test_validate_ip_invalid(self):
        """Test invalid IP validation"""
        assert not SecurityValidator.validate_ip("256.1.1.1")
        assert not SecurityValidator.validate_ip("invalid")
        assert not SecurityValidator.validate_ip("")
        assert not SecurityValidator.validate_ip(None)

    def test_sanitize_path_valid(self):
        """Test path sanitization with valid paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            test_file = base_dir / "test.txt"

            result = SecurityValidator.sanitize_path(str(test_file), base_dir=base_dir)
            assert result is not None
            assert result == test_file.resolve()

    def test_sanitize_path_traversal(self):
        """Test path traversal prevention"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Test various path traversal attempts
            assert (
                SecurityValidator.sanitize_path("../etc/passwd", base_dir=base_dir)
                is None
            )
            assert (
                SecurityValidator.sanitize_path("../../root", base_dir=base_dir) is None
            )
            assert (
                SecurityValidator.sanitize_path("/etc/passwd", base_dir=base_dir)
                is None
            )

    def test_sanitize_command_arg_valid(self):
        """Test command argument sanitization with valid args"""
        assert SecurityValidator.sanitize_command_arg("example.com") == "example.com"
        assert SecurityValidator.sanitize_command_arg("192.168.1.1") == "192.168.1.1"
        assert (
            SecurityValidator.sanitize_command_arg("test-file.txt") == "test-file.txt"
        )

    def test_sanitize_command_arg_injection(self):
        """Test command injection prevention"""
        assert SecurityValidator.sanitize_command_arg("test; rm -rf /") is None
        assert SecurityValidator.sanitize_command_arg("test | cat /etc/passwd") is None
        assert SecurityValidator.sanitize_command_arg("test && malicious") is None
        assert SecurityValidator.sanitize_command_arg("$(whoami)") is None
        assert SecurityValidator.sanitize_command_arg("`whoami`") is None

    def test_sanitize_log_input(self):
        """Test log input sanitization"""
        # Test newline removal
        result = SecurityValidator.sanitize_log_input("test\ninjection")
        assert "\n" not in result
        assert "\r" not in result

        # Test ANSI escape code removal
        result = SecurityValidator.sanitize_log_input("\x1b[31mred text\x1b[0m")
        assert "\x1b" not in result

    def test_sanitize_html(self):
        """Test HTML sanitization"""
        result = SecurityValidator.sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

        result = SecurityValidator.sanitize_html("<img src=x onerror=alert(1)>")
        assert "<img" not in result
        assert "&lt;img" in result


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_rate_limiter_allows_within_limit(self):
        """Test that rate limiter allows calls within limit"""
        limiter = RateLimiter(max_calls=3, time_window=60)

        @limiter
        def test_func(identifier="test"):
            return True

        # Should allow first 3 calls
        assert test_func(identifier="test")
        assert test_func(identifier="test")
        assert test_func(identifier="test")

    def test_rate_limiter_blocks_over_limit(self):
        """Test that rate limiter blocks calls over limit"""
        limiter = RateLimiter(max_calls=2, time_window=60)

        @limiter
        def test_func(identifier="test"):
            return True

        # First 2 calls should succeed
        assert test_func(identifier="test")
        assert test_func(identifier="test")

        # Third call should raise PermissionError
        with pytest.raises(PermissionError):
            test_func(identifier="test")


class TestFilePermissionManager:
    """Test file permission management"""

    def test_set_secure_permissions(self):
        """Test setting secure file permissions"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Set secure permissions
            assert FilePermissionManager.set_secure_permissions(tmp_path, mode=0o600)

            # Verify permissions
            stat_info = os.stat(tmp_path)
            actual_mode = stat_info.st_mode & 0o777
            assert actual_mode == 0o600
        finally:
            tmp_path.unlink()

    def test_verify_permissions(self):
        """Test permission verification"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Set permissions
            os.chmod(tmp_path, 0o600)

            # Verify correct permissions
            assert FilePermissionManager.verify_permissions(
                tmp_path, expected_mode=0o600
            )

            # Verify incorrect permissions detection
            os.chmod(tmp_path, 0o644)
            assert not FilePermissionManager.verify_permissions(
                tmp_path, expected_mode=0o600
            )
        finally:
            tmp_path.unlink()

    def test_create_secure_directory(self):
        """Test secure directory creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "secure_test"

            # Create secure directory
            assert FilePermissionManager.create_secure_directory(test_dir, mode=0o700)

            # Verify it exists and has correct permissions
            assert test_dir.exists()
            stat_info = os.stat(test_dir)
            actual_mode = stat_info.st_mode & 0o777
            assert actual_mode == 0o700


class TestTokenGenerator:
    """Test token generation"""

    def test_generate_token(self):
        """Test token generation"""
        token1 = TokenGenerator.generate_token(32)
        token2 = TokenGenerator.generate_token(32)

        # Tokens should be different
        assert token1 != token2

        # Tokens should be hex strings
        assert all(c in "0123456789abcdef" for c in token1)
        assert all(c in "0123456789abcdef" for c in token2)

    def test_generate_api_key(self):
        """Test API key generation"""
        api_key = TokenGenerator.generate_api_key()

        # Should have prefix
        assert api_key.startswith("vf_")

        # Should be long enough
        assert len(api_key) > 10

    def test_hash_and_verify_token(self):
        """Test token hashing and verification"""
        token = "test_token_12345"

        # Hash token
        hashed = TokenGenerator.hash_token(token)

        # Verify correct token
        assert TokenGenerator.verify_token(token, hashed)

        # Verify incorrect token
        assert not TokenGenerator.verify_token("wrong_token", hashed)


class TestAuthManager:
    """Test authentication manager"""

    def test_create_user(self):
        """Test user creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthManager(auth_dir=Path(tmpdir))

            # Create user
            assert auth_manager.create_user("testuser", Role.USER)

            # Verify user exists
            user = auth_manager.get_user("testuser")
            assert user is not None
            assert user.username == "testuser"
            assert user.role == Role.USER

    def test_create_session(self):
        """Test session creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthManager(auth_dir=Path(tmpdir))
            auth_manager.create_user("testuser", Role.USER)

            # Create session
            session_id = auth_manager.create_session("testuser")
            assert session_id is not None

            # Validate session
            session = auth_manager.validate_session(session_id)
            assert session is not None
            assert session.username == "testuser"

    def test_permission_check(self):
        """Test permission checking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthManager(auth_dir=Path(tmpdir))

            # Create admin and regular user
            auth_manager.create_user("admin", Role.ADMIN)
            auth_manager.create_user("user", Role.USER)

            # Admin should have all permissions
            assert auth_manager.has_permission("admin", Permission.CONFIG_WRITE)
            assert auth_manager.has_permission("admin", Permission.SCAN_AGGRESSIVE)

            # Regular user should not have admin permissions
            assert not auth_manager.has_permission("user", Permission.CONFIG_WRITE)
            assert not auth_manager.has_permission("user", Permission.SCAN_AGGRESSIVE)

            # Regular user should have basic permissions
            assert auth_manager.has_permission("user", Permission.SCAN_TARGET)
            assert auth_manager.has_permission("user", Permission.REPORT_VIEW)


class TestHelperFunctions:
    """Test helper functions"""

    def test_validate_target(self):
        """Test target validation"""
        assert validate_target("example.com")
        assert validate_target("192.168.1.1")
        assert not validate_target("invalid target")
        assert not validate_target("")

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        assert sanitize_filename("test.txt") == "test.txt"
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("file with spaces.txt") == "file_with_spaces.txt"
        assert sanitize_filename("test/path/file.txt") == "file.txt"
