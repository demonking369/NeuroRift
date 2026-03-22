#!/usr/bin/env python3
"""
NeuroRift Security Utilities Module
Provides security functions for input validation, sanitization, and protection
"""

import os
import re
import logging
import hashlib
import secrets
from pathlib import Path
from typing import List, Optional, Any, Callable
from functools import wraps
import time
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Centralized security validation and sanitization"""

    # Dangerous patterns for command injection
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",  # Shell metacharacters
        r"\$\{.*\}",  # Variable expansion
        r"\$\(.*\)",  # Command substitution
        r"`.*`",  # Backtick command substitution
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.",  # Parent directory
        r"~",  # Home directory
        r"/etc/",  # System directories
        r"/root/",
        r"/proc/",
        r"/sys/",
    ]

    @staticmethod
    def validate_domain(domain: str) -> bool:
        """Validate domain name format

        Args:
            domain: Domain name to validate

        Returns:
            True if valid domain, False otherwise
        """
        if not domain or not isinstance(domain, str):
            return False

        # Remove protocol if present
        domain = re.sub(r"^https?://", "", domain)

        # Basic domain validation
        domain_pattern = (
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        )
        return bool(re.match(domain_pattern, domain))

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address format

        Args:
            ip: IP address to validate

        Returns:
            True if valid IP, False otherwise
        """
        if not ip or not isinstance(ip, str):
            return False

        # IPv4 validation
        ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        return bool(re.match(ipv4_pattern, ip))

    @staticmethod
    def sanitize_path(path: str, base_dir: Optional[Path] = None) -> Optional[Path]:
        """Sanitize and validate file path to prevent path traversal

        Args:
            path: Path to sanitize
            base_dir: Base directory to restrict access to

        Returns:
            Sanitized Path object or None if invalid
        """
        if not path or not isinstance(path, str):
            logger.warning("Invalid path provided: %s", path)
            return None

        try:
            # Convert to Path object and resolve
            sanitized = Path(path).resolve()

            # Check for path traversal patterns
            path_str = str(sanitized)
            for pattern in SecurityValidator.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, path_str, re.IGNORECASE):
                    logger.warning("Path traversal attempt detected: %s", path)
                    return None

            # If base_dir provided, ensure path is within it
            if base_dir:
                base_dir = Path(base_dir).resolve()
                try:
                    sanitized.relative_to(base_dir)
                except ValueError:
                    logger.warning("Path outside base directory: %s", path)
                    return None

            return sanitized

        except (ValueError, RuntimeError) as e:
            logger.error("Error sanitizing path %s: %s", path, e)
            return None

    @staticmethod
    def sanitize_command_arg(arg: str) -> Optional[str]:
        """Sanitize command line argument to prevent injection

        Args:
            arg: Argument to sanitize

        Returns:
            Sanitized argument or None if dangerous
        """
        if not arg or not isinstance(arg, str):
            return None

        # Check for command injection patterns
        for pattern in SecurityValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, arg):
                logger.warning("Command injection attempt detected: %s", arg)
                return None

        # Additional validation: only allow alphanumeric, dots, dashes, underscores, slashes
        if not re.match(r"^[a-zA-Z0-9._/-]+$", arg):
            logger.warning("Invalid characters in argument: %s", arg)
            return None

        return arg

    @staticmethod
    def sanitize_log_input(message: str) -> str:
        """Sanitize log message to prevent log injection

        Args:
            message: Log message to sanitize

        Returns:
            Sanitized log message
        """
        if not isinstance(message, str):
            return str(message)

        # Remove newlines and carriage returns
        sanitized = message.replace("\n", " ").replace("\r", " ")

        # Remove ANSI escape codes
        sanitized = re.sub(r"\x1b\[[0-9;]*m", "", sanitized)

        return sanitized

    @staticmethod
    def sanitize_html(html: str) -> str:
        """Sanitize HTML to prevent XSS

        Args:
            html: HTML content to sanitize

        Returns:
            Sanitized HTML
        """
        if not isinstance(html, str):
            return str(html)

        # Basic HTML entity encoding
        html = html.replace("&", "&amp;")
        html = html.replace("<", "&lt;")
        html = html.replace(">", "&gt;")
        html = html.replace('"', "&quot;")
        html = html.replace("'", "&#x27;")

        return html

    @staticmethod
    def validate_json_schema(data: dict, required_keys: List[str]) -> bool:
        """Validate JSON data against required schema

        Args:
            data: JSON data to validate
            required_keys: List of required keys

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            return False

        for key in required_keys:
            if key not in data:
                logger.warning("Missing required key in JSON: %s", key)
                return False

        return True


class RateLimiter:
    """Rate limiting decorator for sensitive operations"""

    def __init__(self, max_calls: int = 10, time_window: int = 60):
        """Initialize rate limiter

        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = defaultdict(list)
        self.lock = threading.Lock()

    def __call__(self, func: Callable) -> Callable:
        """Decorator to rate limit function calls"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get identifier (could be IP, user ID, etc.)
            identifier = kwargs.get("identifier", "default")

            with self.lock:
                now = time.time()

                # Remove old calls outside time window
                self.calls[identifier] = [
                    call_time
                    for call_time in self.calls[identifier]
                    if now - call_time < self.time_window
                ]

                # Check if rate limit exceeded
                if len(self.calls[identifier]) >= self.max_calls:
                    logger.warning("Rate limit exceeded for %s", identifier)
                    raise PermissionError(
                        f"Rate limit exceeded. Maximum {self.max_calls} calls "
                        f"per {self.time_window} seconds."
                    )

                # Record this call
                self.calls[identifier].append(now)

            return func(*args, **kwargs)

        return wrapper


class FilePermissionManager:
    """Manage secure file permissions"""

    @staticmethod
    def set_secure_permissions(filepath: Path, mode: int = 0o600) -> bool:
        """Set secure file permissions

        Args:
            filepath: Path to file
            mode: Permission mode (default: 0o600 - owner read/write only)

        Returns:
            True if successful, False otherwise
        """
        try:
            os.chmod(filepath, mode)
            logger.info("Set secure permissions %o on %s", mode, filepath)
            return True
        except (OSError, PermissionError) as e:
            logger.error("Failed to set permissions on %s: %s", filepath, e)
            return False

    @staticmethod
    def verify_permissions(filepath: Path, expected_mode: int = 0o600) -> bool:
        """Verify file has expected permissions

        Args:
            filepath: Path to file
            expected_mode: Expected permission mode

        Returns:
            True if permissions match, False otherwise
        """
        try:
            stat_info = os.stat(filepath)
            actual_mode = stat_info.st_mode & 0o777

            if actual_mode != expected_mode:
                logger.warning(
                    "Insecure permissions on %s: %o (expected %o)",
                    filepath,
                    actual_mode,
                    expected_mode,
                )
                return False

            return True

        except (OSError, FileNotFoundError) as e:
            logger.error("Error checking permissions on %s: %s", filepath, e)
            return False

    @staticmethod
    def create_secure_directory(dirpath: Path, mode: int = 0o700) -> bool:
        """Create directory with secure permissions

        Args:
            dirpath: Path to directory
            mode: Permission mode (default: 0o700 - owner only)

        Returns:
            True if successful, False otherwise
        """
        try:
            dirpath.mkdir(parents=True, exist_ok=True, mode=mode)
            # Ensure permissions are set correctly (mkdir mode can be affected by umask)
            os.chmod(dirpath, mode)
            logger.info("Created secure directory %s with mode %o", dirpath, mode)
            return True
        except (OSError, PermissionError) as e:
            logger.error("Failed to create secure directory %s: %s", dirpath, e)
            return False


class TokenGenerator:
    """Generate secure tokens for sessions and API keys"""

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate cryptographically secure random token

        Args:
            length: Length of token in bytes

        Returns:
            Hex-encoded token
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_api_key() -> str:
        """Generate API key with prefix

        Returns:
            API key string
        """
        prefix = "vf_"
        token = secrets.token_urlsafe(32)
        return f"{prefix}{token}"

    @staticmethod
    def hash_token(token: str, salt: Optional[str] = None) -> str:
        """Hash token for secure storage

        Args:
            token: Token to hash
            salt: Optional salt (generated if not provided)

        Returns:
            Hashed token
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # Use SHA-256 for hashing
        hash_obj = hashlib.sha256()
        hash_obj.update(f"{salt}{token}".encode("utf-8"))

        return f"{salt}:{hash_obj.hexdigest()}"

    @staticmethod
    def verify_token(token: str, hashed: str) -> bool:
        """Verify token against hash

        Args:
            token: Token to verify
            hashed: Hashed token (salt:hash format)

        Returns:
            True if token matches, False otherwise
        """
        try:
            salt, expected_hash = hashed.split(":", 1)

            hash_obj = hashlib.sha256()
            hash_obj.update(f"{salt}{token}".encode("utf-8"))
            actual_hash = hash_obj.hexdigest()

            # Use constant-time comparison to prevent timing attacks
            return secrets.compare_digest(actual_hash, expected_hash)

        except (ValueError, AttributeError):
            return False


# Convenience functions
def validate_target(target: str) -> bool:
    """Validate target is either valid domain or IP

    Args:
        target: Target to validate

    Returns:
        True if valid, False otherwise
    """
    return SecurityValidator.validate_domain(target) or SecurityValidator.validate_ip(
        target
    )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)

    # Remove dangerous characters
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    return filename
