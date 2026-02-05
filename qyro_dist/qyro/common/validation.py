"""
Nexus Input Validation and Sanitization
Production-grade validation and sanitization for secure data handling.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from .errors import NexusError, ErrorCode, JSONError, Result
import html
import urllib.parse


class ValidationError(NexusError):
    """Specific exception for validation errors."""
    pass


class InputValidator:
    """
    Production-grade input validation system with multiple layers of security.
    """
    
    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        # SQL injection patterns
        r"(?i)(union\s+select|drop\s+\w+|delete\s+from|insert\s+into|update\s+\w+\s+set)",
        # Command injection patterns
        r"(?i)(exec|system|popen|subprocess|os\.)",
        # Path traversal
        r"(\.\.\/|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
        # JavaScript injection
        r"(?i)(<script|javascript:|on\w+\s*=)",
        # File inclusion
        r"(?i)(include|require|open\()",
        # Network operations
        r"(?i)(socket|connect|bind|listen|accept|urlopen|request)",
    ]
    
    # Safe patterns for different contexts
    SAFE_PATTERNS = {
        'identifier': r'^[a-zA-Z_][a-zA-Z0-9_]*$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'url': r'^https?://[^\s/$.?#].[^\s]*$',
        'phone': r'^\+?[\d\s\-\(\)]+$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'alpha': r'^[a-zA-Z]+$',
        'numeric': r'^\d+$',
    }

    @classmethod
    def validate_pattern(cls, value: str, pattern_name: str) -> bool:
        """
        Validate a string against a predefined safe pattern.
        
        Args:
            value: String to validate
            pattern_name: Name of the pattern to use
            
        Returns:
            True if valid, False otherwise
        """
        if pattern_name not in cls.SAFE_PATTERNS:
            raise ValidationError(ErrorCode.JSON_PARSE_ERROR, f"Unknown pattern: {pattern_name}")
        
        pattern = cls.SAFE_PATTERNS[pattern_name]
        return bool(re.match(pattern, value))

    @classmethod
    def validate_dangerous_content(cls, value: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a string contains dangerous patterns.
        
        Args:
            value: String to check
            
        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        for i, pattern in enumerate(cls.DANGEROUS_PATTERNS):
            if re.search(pattern, value, re.IGNORECASE):
                return False, f"Dangerous pattern #{i+1} detected"
        return True, None

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000, allow_html: bool = False) -> str:
        """
        Sanitize a string input with multiple layers of protection.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML (will be escaped if False)
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Truncate to max length
        value = value[:max_length]

        # Remove null bytes
        value = value.replace('\x00', '')

        if not allow_html:
            # Escape HTML entities
            value = html.escape(value, quote=True)

        return value

    @classmethod
    def sanitize_json(cls, data: Union[Dict, List, str], max_depth: int = 10) -> Union[Dict, List]:
        """
        Recursively sanitize JSON data with depth protection.
        
        Args:
            data: JSON data to sanitize
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized JSON data
        """
        return cls._sanitize_json_recursive(data, max_depth, 0)

    @classmethod
    def _sanitize_json_recursive(cls, data: Any, max_depth: int, current_depth: int) -> Any:
        """Helper method for recursive sanitization."""
        if current_depth > max_depth:
            raise ValidationError(ErrorCode.JSON_PARSE_ERROR, f"JSON exceeds maximum depth of {max_depth}")

        if isinstance(data, str):
            return cls.sanitize_string(data)
        elif isinstance(data, dict):
            return {k: cls._sanitize_json_recursive(v, max_depth, current_depth + 1) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls._sanitize_json_recursive(item, max_depth, current_depth + 1) for item in data]
        else:
            return data

    @classmethod
    def validate_json_structure(cls, data: Dict, schema: Dict, path: str = "root") -> List[str]:
        """
        Validate JSON data against a schema with detailed error reporting.
        
        Args:
            data: Data to validate
            schema: Schema to validate against
            path: Current path in the validation (for error reporting)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for key, expected_type in schema.items():
            full_path = f"{path}.{key}" if path != "root" else key
            
            if key not in data:
                if isinstance(expected_type, dict) and expected_type.get('_required', True):
                    errors.append(f"Missing required field: {full_path}")
                continue

            actual_value = data[key]
            actual_type = type(actual_value)
            expected_python_type = cls._get_python_type(expected_type)

            if actual_type != expected_python_type:
                # Allow int for float fields
                if not (expected_python_type == float and actual_type == int):
                    errors.append(f"Type mismatch at {full_path}: expected {expected_python_type.__name__}, got {actual_type.__name__}")
                    continue

            # Validate nested objects
            if isinstance(expected_type, dict) and '_type' not in expected_type:
                if isinstance(actual_value, dict):
                    errors.extend(cls.validate_json_structure(actual_value, expected_type, full_path))
                else:
                    errors.append(f"Expected object at {full_path}, got {actual_type.__name__}")

        return errors

    @classmethod
    def _get_python_type(cls, expected_type: Any) -> type:
        """Convert schema type to Python type."""
        type_mapping = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
            str: str,
            int: int,
            float: float,
            bool: bool,
            list: list,
            dict: dict,
        }
        
        if isinstance(expected_type, str):
            return type_mapping.get(expected_type, str)
        elif isinstance(expected_type, type):
            return expected_type
        else:
            return type(expected_type) if expected_type else type(None)


class SchemaValidator:
    """
    Advanced schema validation with type safety and structure consistency.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.validator = InputValidator()

    def validate(self, data: Dict[str, Any]) -> Result:
        """
        Validate data against schema with comprehensive error reporting.
        
        Args:
            data: Data to validate against schema
            
        Returns:
            Result object with validation outcome
        """
        try:
            # First, check for dangerous content
            sanitized_data = self.validator.sanitize_json(data)
            
            # Then validate structure
            errors = self.validator.validate_json_structure(sanitized_data, self.schema)
            
            if errors:
                return Result.err(ValidationError(
                    ErrorCode.JSON_SCHEMA_MISMATCH,
                    f"Schema validation failed: {'; '.join(errors)}"
                ))
                
            return Result.ok(sanitized_data)
        except Exception as e:
            return Result.err(ValidationError(
                ErrorCode.JSON_PARSE_ERROR,
                f"Validation error: {str(e)}"
            ))


class RateLimiter:
    """
    Production-grade token bucket rate limiter with sliding window support.
    """
    
    def __init__(self, rate: int = 100, per_seconds: int = 60):
        self.rate = rate
        self.per_seconds = per_seconds
        self._buckets: Dict[str, Dict] = {}
        import threading
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for given key with thread safety.
        
        Args:
            key: Identifier for the rate limiting bucket
            
        Returns:
            True if allowed, False if rate limited
        """
        import time
        now = time.time()

        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = {
                    "tokens": self.rate,
                    "last_update": now
                }

            bucket = self._buckets[key]

            # Refill tokens based on time passed
            time_passed = now - bucket["last_update"]
            tokens_to_add = time_passed * (self.rate / self.per_seconds)
            bucket["tokens"] = min(self.rate, bucket["tokens"] + tokens_to_add)
            bucket["last_update"] = now

            # Check if we have a token available
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True

            return False

    def get_retry_after(self, key: str) -> float:
        """
        Get seconds until next request is allowed.
        
        Args:
            key: Identifier for the rate limiting bucket
            
        Returns:
            Seconds until next request is allowed
        """
        if key not in self._buckets:
            return 0

        with self._lock:
            bucket = self._buckets[key]
            if bucket["tokens"] >= 1:
                return 0

            tokens_needed = 1 - bucket["tokens"]
            return tokens_needed * (self.per_seconds / self.rate)


class InputSanitizer:
    """
    Comprehensive input sanitization system.
    """
    
    @classmethod
    def sanitize_for_sql(cls, value: str) -> str:
        """Sanitize input for SQL queries."""
        # Remove dangerous SQL keywords and characters
        dangerous_sql = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'EXEC', 
            'UNION', 'SELECT', 'WHERE', 'FROM', 'JOIN', '--', ';', '/*', '*/'
        ]
        
        result = value
        for sql_keyword in dangerous_sql:
            # Case insensitive replacement
            result = re.sub(sql_keyword, '', result, flags=re.IGNORECASE)
        
        # Remove SQL comment patterns
        result = re.sub(r'/\*.*?\*/', '', result)  # Block comments
        result = re.sub(r'--.*', '', result)       # Line comments
        
        return result.strip()

    @classmethod
    def sanitize_for_shell(cls, value: str) -> str:
        """Sanitize input for shell commands."""
        # Remove shell metacharacters
        dangerous_chars = [';', '|', '&', '`', '$', '(', ')', '<', '>']
        result = value
        for char in dangerous_chars:
            result = result.replace(char, '')
        
        return result.strip()

    @classmethod
    def sanitize_for_html(cls, value: str) -> str:
        """Sanitize input for HTML output."""
        return html.escape(value, quote=True)

    @classmethod
    def sanitize_for_url(cls, value: str) -> str:
        """Sanitize input for URL usage."""
        return urllib.parse.quote(value, safe='/:?#[]@!$&\'()*+,;=')


# Global validator instance
_global_validator = None


def get_validator() -> InputValidator:
    """Get the global input validator instance."""
    global _global_validator
    if _global_validator is None:
        _global_validator = InputValidator()
    return _global_validator


def validate_input(value: str, pattern_name: str = None) -> Tuple[bool, str]:
    """
    Convenience function to validate input.
    
    Args:
        value: Value to validate
        pattern_name: Optional pattern name to validate against
        
    Returns:
        Tuple of (is_valid, message)
    """
    validator = get_validator()
    
    if pattern_name:
        if validator.validate_pattern(value, pattern_name):
            return True, "Valid input"
        else:
            return False, f"Does not match pattern: {pattern_name}"
    
    is_safe, reason = validator.validate_dangerous_content(value)
    if is_safe:
        return True, "Valid input"
    else:
        return False, f"Contains dangerous content: {reason}"