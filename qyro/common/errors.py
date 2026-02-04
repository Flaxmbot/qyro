"""
Qyro Error Handling Framework
Standardized error codes and exception classes for cross-language consistency.
"""

from enum import IntEnum
from typing import Dict, Any, Optional


class ErrorCode(IntEnum):
    """Standardized error codes across all Qyro components."""

    # Success
    SUCCESS = 0

    # Memory Errors (1xxx)
    MEMORY_NOT_FOUND = 1001
    MEMORY_LOCK_TIMEOUT = 1002
    MEMORY_CORRUPTION = 1003
    MEMORY_FULL = 1004
    MEMORY_ACCESS_DENIED = 1005

    # JSON/Schema Errors (2xxx)
    JSON_PARSE_ERROR = 2001
    JSON_SCHEMA_MISMATCH = 2002
    JSON_ENCODE_ERROR = 2003
    SCHEMA_NOT_FOUND = 2004
    SCHEMA_INVALID = 2005

    # Auth Errors (3xxx)
    AUTH_FAILED = 3001
    AUTH_EXPIRED = 3002
    AUTH_INVALID_TOKEN = 3003
    AUTH_PERMISSION_DENIED = 3004

    # Slot Errors (4xxx)
    SLOT_OVERFLOW = 4001
    SLOT_NOT_FOUND = 4002
    SLOT_LOCKED = 4003

    # Process Errors (5xxx)
    PROCESS_SPAWN_FAILED = 5001
    PROCESS_CRASH = 5002
    PROCESS_TIMEOUT = 5003

    # Compile Errors (6xxx)
    COMPILE_C_FAILED = 6001
    COMPILE_RUST_FAILED = 6002
    COMPILE_JAVA_FAILED = 6003
    COMPILE_GO_FAILED = 6004

    # Parse Errors (7xxx)
    PARSE_FILE_NOT_FOUND = 7001
    PARSE_INVALID_BLOCK = 7002
    PARSE_IMPORT_FAILED = 7003

    # Security Errors (8xxx)
    SECURITY_VIOLATION = 8001
    INPUT_VALIDATION_FAILED = 8002
    RESOURCE_LIMIT_EXCEEDED = 8003
    UNTRUSTED_CODE_REJECTED = 8004


class QyroError(Exception):
    """Base exception for all Qyro errors."""
    def __init__(self, code: ErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code.value}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "code": self.code.value,
            "message": self.message,
            "details": self.details
        }


class ErrorCode:
    """Standardized error codes across all Qyro components."""
    
    # Success
    SUCCESS = 0
    
    # Memory Errors (1xxx)
    MEMORY_NOT_FOUND = 1001
    MEMORY_LOCK_TIMEOUT = 1002
    MEMORY_CORRUPTION = 1003
    MEMORY_FULL = 1004
    MEMORY_ACCESS_DENIED = 1005
    
    # JSON/Schema Errors (2xxx)
    JSON_PARSE_ERROR = 2001
    JSON_SCHEMA_MISMATCH = 2002
    JSON_ENCODE_ERROR = 2003
    SCHEMA_NOT_FOUND = 2004
    SCHEMA_INVALID = 2005
    
    # Auth Errors (3xxx)
    AUTH_FAILED = 3001
    AUTH_EXPIRED = 3002
    AUTH_INVALID_TOKEN = 3003
    AUTH_PERMISSION_DENIED = 3004
    
    # Slot Errors (4xxx)
    SLOT_OVERFLOW = 4001
    SLOT_NOT_FOUND = 4002
    SLOT_LOCKED = 4003
    
    # Process Errors (5xxx)
    PROCESS_SPAWN_FAILED = 5001
    PROCESS_CRASH = 5002
    PROCESS_TIMEOUT = 5003
    
    # Compile Errors (6xxx)
    COMPILE_C_FAILED = 6001
    COMPILE_RUST_FAILED = 6002
    COMPILE_JAVA_FAILED = 6003
    COMPILE_GO_FAILED = 6004
    
    # Parse Errors (7xxx)
    PARSE_FILE_NOT_FOUND = 7001
    PARSE_INVALID_BLOCK = 7002
    PARSE_IMPORT_FAILED = 7003


# Specific exception classes for common error types
class MemoryError(QyroError):
    def __init__(self, code: ErrorCode = ErrorCode.MEMORY_NOT_FOUND, message: str = "Memory access error", **details):
        super().__init__(code, message, details)


class JSONError(QyroError):
    def __init__(self, code: ErrorCode = ErrorCode.JSON_PARSE_ERROR, message: str = "JSON error", **details):
        super().__init__(code, message, details)


class AuthError(QyroError):
    def __init__(self, code: ErrorCode = ErrorCode.AUTH_FAILED, message: str = "Authentication error", **details):
        super().__init__(code, message, details)


class CompileError(QyroError):
    def __init__(self, code: ErrorCode = ErrorCode.COMPILE_C_FAILED, message: str = "Compilation error", **details):
        super().__init__(code, message, details)


class ParseError(QyroError):
    def __init__(self, code: 'ErrorCode' = None, message: str = "Parse error", **details):
        if code is None:
            code = ErrorCode.PARSE_FILE_NOT_FOUND
        super().__init__(code, message, details)


class SecurityError(QyroError):
    def __init__(self, code: 'ErrorCode' = None, message: str = "Security violation", **details):
        if code is None:
            code = ErrorCode.SECURITY_VIOLATION
        super().__init__(code, message, details)


class ValidationError(QyroError):
    def __init__(self, code: 'ErrorCode' = None, message: str = "Input validation failed", **details):
        if code is None:
            code = ErrorCode.INPUT_VALIDATION_FAILED
        super().__init__(code, message, details)


class ResourceLimitError(QyroError):
    def __init__(self, code: 'ErrorCode' = None, message: str = "Resource limit exceeded", **details):
        if code is None:
            code = ErrorCode.RESOURCE_LIMIT_EXCEEDED
        super().__init__(code, message, details)


# Result type for operations that can fail
class Result:
    """Rust-style Result type for safe error handling."""

    def __init__(self, value=None, error: QyroError = None):
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, value):
        return cls(value=value)

    @classmethod
    def err(cls, error: QyroError):
        return cls(error=error)

    def is_ok(self) -> bool:
        return self._error is None

    def is_err(self) -> bool:
        return self._error is not None

    def unwrap(self):
        if self._error:
            raise self._error
        return self._value

    def unwrap_or(self, default):
        return self._value if self._error is None else default

    def map(self, fn):
        if self._error:
            return self
        try:
            return Result.ok(fn(self._value))
        except QyroError as e:
            return Result.err(e)

    def __repr__(self):
        if self._error:
            return f"Err({self._error})"
        return f"Ok({self._value})"


# Qyro compatibility aliases
QyroError = NexusError
QyroErrorCode = ErrorCode
