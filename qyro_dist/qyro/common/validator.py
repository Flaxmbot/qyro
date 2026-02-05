"""
Nexus Input Validation
Schema validation and input sanitization for safe data handling.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union
from .errors import NexusError, ErrorCode, JSONError, Result


class SchemaValidator:
    """
    Validates JSON data against a schema definition.
    Ensures type safety and structure consistency.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self._type_map = {
            str: "string",
            int: "integer", 
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null"
        }
    
    def validate(self, data: Dict[str, Any]) -> Result:
        """
        Validate data against schema.
        Returns Result.ok(data) if valid, Result.err(error) if invalid.
        """
        try:
            self._validate_object(data, self.schema, "root")
            return Result.ok(data)
        except NexusError as e:
            return Result.err(e)
    
    def _validate_object(self, data: Dict, schema: Dict, path: str):
        """Recursively validate object structure."""
        if not isinstance(data, dict):
            raise JSONError(
                ErrorCode.JSON_SCHEMA_MISMATCH,
                f"Expected object at {path}, got {type(data).__name__}"
            )
        
        for key, expected_value in schema.items():
            field_path = f"{path}.{key}"
            
            if key not in data:
                # Check if it's a required field (non-null in schema)
                if expected_value is not None:
                    continue  # Allow missing optional fields
            
            actual_value = data.get(key)
            
            if isinstance(expected_value, dict):
                self._validate_object(actual_value, expected_value, field_path)
            elif isinstance(expected_value, list):
                self._validate_array(actual_value, expected_value, field_path)
            else:
                self._validate_type(actual_value, expected_value, field_path)
    
    def _validate_array(self, data: List, schema_array: List, path: str):
        """Validate array elements."""
        if not isinstance(data, list):
            raise JSONError(
                ErrorCode.JSON_SCHEMA_MISMATCH,
                f"Expected array at {path}, got {type(data).__name__}"
            )
        
        if schema_array and len(schema_array) > 0:
            element_schema = schema_array[0]
            for i, item in enumerate(data):
                item_path = f"{path}[{i}]"
                if isinstance(element_schema, dict):
                    self._validate_object(item, element_schema, item_path)
                else:
                    self._validate_type(item, element_schema, item_path)
    
    def _validate_type(self, value: Any, expected: Any, path: str):
        """Validate primitive types."""
        expected_type = type(expected)
        actual_type = type(value)
        
        # Allow int for float fields
        if expected_type == float and actual_type == int:
            return
        
        # Allow None for any field
        if value is None:
            return
        
        if actual_type != expected_type:
            raise JSONError(
                ErrorCode.JSON_SCHEMA_MISMATCH,
                f"Type mismatch at {path}: expected {expected_type.__name__}, got {actual_type.__name__}"
            )


class InputSanitizer:
    """
    Sanitizes user input to prevent injection and ensure safety.
    """
    
    # Patterns for dangerous content
    DANGEROUS_PATTERNS = [
        re.compile(r'<script\b[^>]*>[\s\S]*?</script>', re.IGNORECASE),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        """Sanitize a string input."""
        if not isinstance(value, str):
            return str(value)
        
        # Truncate to max length
        value = value[:max_length]
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Escape HTML entities
        value = (value
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))
        
        return value
    
    @classmethod
    def sanitize_json(cls, data: Union[Dict, List, str]) -> Union[Dict, List]:
        """Recursively sanitize JSON data."""
        if isinstance(data, str):
            return cls.sanitize_string(data)
        elif isinstance(data, dict):
            return {k: cls.sanitize_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_json(item) for item in data]
        else:
            return data
    
    @classmethod
    def is_safe(cls, value: str) -> bool:
        """Check if a string is safe (no dangerous patterns)."""
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.search(value):
                return False
        return True


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints.
    """
    
    def __init__(self, rate: int = 100, per_seconds: int = 60):
        self.rate = rate
        self.per_seconds = per_seconds
        self._buckets: Dict[str, Dict] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        import time
        now = time.time()
        
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
        """Get seconds until next request is allowed."""
        if key not in self._buckets:
            return 0
        
        bucket = self._buckets[key]
        if bucket["tokens"] >= 1:
            return 0
        
        tokens_needed = 1 - bucket["tokens"]
        return tokens_needed * (self.per_seconds / self.rate)
