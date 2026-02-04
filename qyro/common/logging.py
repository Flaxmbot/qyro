"""
Qyro Structured Logging
JSON-based logging with severity levels for cross-language consistency.
"""

import json
import sys
import time
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, Optional
from pathlib import Path


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class QyroLogger:
    """
    Structured JSON logger for Qyro system.
    Outputs machine-readable logs that can be aggregated across languages.
    """

    _instances: Dict[str, 'QyroLogger'] = {}

    def __init__(
        self,
        name: str = "qyro",
        level: LogLevel = LogLevel.INFO,
        output_file: Optional[str] = None,
        json_output: bool = True
    ):
        self.name = name
        self.level = level
        self.json_output = json_output
        self._file = None
        
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            self._file = open(output_file, 'a', encoding='utf-8')
    
    @classmethod
    def get_logger(cls, name: str = "qyro") -> 'QyroLogger':
        """Get or create a logger instance."""
        if name not in cls._instances:
            cls._instances[name] = cls(name)
        return cls._instances[name]
    
    def _format_message(
        self,
        level: LogLevel,
        message: str,
        **context
    ) -> str:
        """Format log message as JSON or plain text."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        if self.json_output:
            log_entry = {
                "timestamp": timestamp,
                "level": level.name,
                "logger": self.name,
                "message": message,
                **context
            }
            return json.dumps(log_entry, default=str)
        else:
            ctx_str = " ".join(f"{k}={v}" for k, v in context.items())
            return f"[{timestamp}] [{level.name}] [{self.name}] {message} {ctx_str}".strip()
    
    def _log(self, level: LogLevel, message: str, **context):
        """Internal log method."""
        if level < self.level:
            return
        
        formatted = self._format_message(level, message, **context)
        
        # Output to stderr for errors, stdout for others
        output = sys.stderr if level >= LogLevel.ERROR else sys.stdout
        try:
            print(formatted, file=output, flush=True)
        except UnicodeEncodeError:
            # Fallback for Windows consoles: use the stream's own encoding with replacements
            encoding = getattr(output, 'encoding', 'utf-8') or 'utf-8'
            safe_msg = formatted.encode(encoding, errors='replace').decode(encoding)
            print(safe_msg, file=output, flush=True)
        
        # Also write to file if configured
        if self._file:
            print(formatted, file=self._file, flush=True)
    
    def debug(self, message: str, **context):
        self._log(LogLevel.DEBUG, message, **context)
    
    def info(self, message: str, **context):
        self._log(LogLevel.INFO, message, **context)
    
    def warning(self, message: str, **context):
        self._log(LogLevel.WARNING, message, **context)
    
    def error(self, message: str, **context):
        self._log(LogLevel.ERROR, message, **context)
    
    def critical(self, message: str, **context):
        self._log(LogLevel.CRITICAL, message, **context)
    
    def exception(self, message: str, exc: Exception, **context):
        """Log exception with traceback info."""
        import traceback
        context['exception_type'] = type(exc).__name__
        context['exception_message'] = str(exc)
        context['traceback'] = traceback.format_exc()
        self._log(LogLevel.ERROR, message, **context)
    
    def close(self):
        if self._file:
            self._file.close()


def get_logger(name: str = "qyro") -> QyroLogger:
    """Get a named logger instance."""
    return QyroLogger.get_logger(name)


def set_log_level(level: LogLevel):
    """Set the global log level."""
    get_logger().level = level


# Convenience functions
def debug(message: str, **context):
    get_logger().debug(message, **context)

def info(message: str, **context):
    get_logger().info(message, **context)

def warning(message: str, **context):
    get_logger().warning(message, **context)

def error(message: str, **context):
    get_logger().error(message, **context)

def critical(message: str, **context):
    get_logger().critical(message, **context)
