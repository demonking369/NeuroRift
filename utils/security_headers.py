#!/usr/bin/env python3
"""
NeuroRift Security Headers Module
Provides security headers for web responses and API endpoints
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SecurityHeaders:
    """Security headers configuration"""

    # Content Security Policy
    csp: Optional[str] = None

    # HTTP Strict Transport Security
    hsts: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    # X-Frame-Options
    x_frame_options: str = "DENY"

    # X-Content-Type-Options
    x_content_type_options: bool = True

    # X-XSS-Protection
    x_xss_protection: bool = True

    # Referrer-Policy
    referrer_policy: str = "strict-origin-when-cross-origin"

    # Permissions-Policy
    permissions_policy: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary of header name: value pairs

        Returns:
            Dictionary of security headers
        """
        headers = {}

        # Content Security Policy
        if self.csp:
            headers["Content-Security-Policy"] = self.csp
        else:
            # Default restrictive CSP
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

        # HSTS
        if self.hsts:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value

        # X-Frame-Options
        headers["X-Frame-Options"] = self.x_frame_options

        # X-Content-Type-Options
        if self.x_content_type_options:
            headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection
        if self.x_xss_protection:
            headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy
        headers["Referrer-Policy"] = self.referrer_policy

        # Permissions-Policy
        if self.permissions_policy:
            headers["Permissions-Policy"] = self.permissions_policy
        else:
            # Default restrictive permissions policy
            headers["Permissions-Policy"] = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            )

        return headers


class SecurityHeadersManager:
    """Manages security headers for different contexts"""

    # Predefined security header profiles
    PROFILES = {
        "strict": SecurityHeaders(
            x_frame_options="DENY",
            hsts=True,
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=True,
        ),
        "moderate": SecurityHeaders(
            x_frame_options="SAMEORIGIN",
            hsts=True,
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=False,
        ),
        "relaxed": SecurityHeaders(
            x_frame_options="SAMEORIGIN",
            hsts=True,
            hsts_max_age=86400,  # 1 day
            hsts_include_subdomains=False,
            hsts_preload=False,
        ),
    }

    @staticmethod
    def get_headers(profile: str = "strict") -> Dict[str, str]:
        """Get security headers for a profile

        Args:
            profile: Security profile name ('strict', 'moderate', 'relaxed')

        Returns:
            Dictionary of security headers
        """
        if profile not in SecurityHeadersManager.PROFILES:
            profile = "strict"

        return SecurityHeadersManager.PROFILES[profile].to_dict()

    @staticmethod
    def get_api_headers() -> Dict[str, str]:
        """Get security headers for API endpoints

        Returns:
            Dictionary of API security headers
        """
        headers = SecurityHeadersManager.get_headers("strict")

        # Additional API-specific headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        headers["Pragma"] = "no-cache"

        return headers

    @staticmethod
    def get_report_headers() -> Dict[str, str]:
        """Get security headers for report pages

        Returns:
            Dictionary of report security headers
        """
        # Use moderate profile for reports (may need to embed images, etc.)
        headers = SecurityHeadersManager.get_headers("moderate")

        # Allow inline styles for report formatting
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "frame-ancestors 'none'"
        )

        return headers

    @staticmethod
    def apply_headers_to_response(
        response_headers: Dict[str, str], security_profile: str = "strict"
    ) -> Dict[str, str]:
        """Apply security headers to existing response headers

        Args:
            response_headers: Existing response headers
            security_profile: Security profile to apply

        Returns:
            Updated response headers
        """
        security_headers = SecurityHeadersManager.get_headers(security_profile)

        # Merge headers (security headers take precedence)
        updated_headers = {**response_headers, **security_headers}

        return updated_headers


def get_cors_headers(
    allowed_origins: List[str] = None,
    allowed_methods: List[str] = None,
    allowed_headers: List[str] = None,
    max_age: int = 86400,
) -> Dict[str, str]:
    """Get CORS headers for API endpoints

    Args:
        allowed_origins: List of allowed origins (default: none)
        allowed_methods: List of allowed HTTP methods
        allowed_headers: List of allowed headers
        max_age: Max age for preflight cache in seconds

    Returns:
        Dictionary of CORS headers
    """
    headers = {}

    # Access-Control-Allow-Origin
    if allowed_origins:
        # For security, never use '*' in production
        # Instead, validate and return specific origin
        headers["Access-Control-Allow-Origin"] = ", ".join(allowed_origins)

    # Access-Control-Allow-Methods
    if allowed_methods:
        headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
    else:
        headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    # Access-Control-Allow-Headers
    if allowed_headers:
        headers["Access-Control-Allow-Headers"] = ", ".join(allowed_headers)
    else:
        headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

    # Access-Control-Max-Age
    headers["Access-Control-Max-Age"] = str(max_age)

    # Access-Control-Allow-Credentials
    headers["Access-Control-Allow-Credentials"] = "true"

    return headers


def sanitize_response_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Remove potentially sensitive headers from response

    Args:
        headers: Response headers

    Returns:
        Sanitized headers
    """
    # Headers that should be removed to prevent information disclosure
    sensitive_headers = [
        "Server",
        "X-Powered-By",
        "X-AspNet-Version",
        "X-AspNetMvc-Version",
        "X-Runtime",
    ]

    sanitized = {k: v for k, v in headers.items() if k not in sensitive_headers}

    return sanitized
