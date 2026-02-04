"""
Nexus Core Constants
Global constants shared across all language adapters for consistency.
"""

# Version
NEXUS_VERSION = "2.0.0"
PROTOCOL_VERSION = 3

# File Names - MUST match across all adapters
MEM_FILE = "nexus.mem"
LOCK_FILE = ".nexus_global.lock"  # UNIFIED lock file for ALL adapters

# Memory Layout - NBP v3 (Nexus Binary Protocol)
# All offsets in bytes, all integers are little-endian
HEADER_SIZE = 32

# Header offsets
OFFSET_MAGIC = 0          # [0-4]:   Magic bytes "NEXS"
OFFSET_VERSION = 4        # [4-8]:   Protocol version (3)
OFFSET_SEQUENCE = 8       # [8-12]:  Sequence number for optimistic concurrency
OFFSET_CHECKSUM = 12      # [12-16]: CRC32 checksum of data
OFFSET_REGISTRY = 16      # [16-20]: Registry offset (function registry start)
OFFSET_LENGTH = 20        # [20-24]: Data length
OFFSET_FLAGS = 24         # [24-28]: Flags (encrypted, compressed, etc.)
OFFSET_RESERVED = 28      # [28-32]: Reserved for future use
OFFSET_DATA = 32          # [32...]: JSON/binary data

# Magic bytes
MAGIC_BYTES = b"NEXS"

# Default sizes
DEFAULT_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
SLOT_SIZE = 1024  # 1 KB per slot
MAX_SLOTS = 1000  # Maximum number of slots

# Function Calling - Reserved memory regions
REGISTRY_OFFSET = 1024           # Function registry starts at 1KB
REGISTRY_SIZE = 1024             # 1KB for registry
CALL_QUEUE_OFFSET = 2048         # Call queue starts at 2KB  
CALL_QUEUE_SIZE = 2048           # 2KB for call queue
RESULT_QUEUE_OFFSET = 4096       # Result queue starts at 4KB
RESULT_QUEUE_SIZE = 4096         # 4KB for result queue
DATA_OFFSET = 8192               # User data starts at 8KB

# Timeouts (in seconds)
DEFAULT_LOCK_TIMEOUT = 5.0
DEFAULT_CALL_TIMEOUT = 30.0
DEFAULT_POLL_INTERVAL = 0.05     # 50ms for polling mode

# Flags (bitmask)
FLAG_ENCRYPTED = 0x01
FLAG_COMPRESSED = 0x02
FLAG_BINARY = 0x04               # MessagePack instead of JSON

# Error codes - must match across all languages
class ErrorCode:
    # Memory errors (1xxx)
    MEMORY_NOT_FOUND = 1001
    MEMORY_LOCK_TIMEOUT = 1002
    MEMORY_CORRUPTION = 1003
    MEMORY_FULL = 1004
    SLOT_OVERFLOW = 1005
    CHECKSUM_MISMATCH = 1006
    VERSION_MISMATCH = 1007

    # JSON errors (2xxx)
    JSON_PARSE_ERROR = 2001
    JSON_ENCODE_ERROR = 2002
    JSON_SCHEMA_MISMATCH = 2003

    # Function call errors (3xxx)
    FUNCTION_NOT_FOUND = 3001
    FUNCTION_TIMEOUT = 3002
    FUNCTION_ERROR = 3003
    INVALID_ARGUMENTS = 3004
    PERMISSION_DENIED = 3005

    # Auth errors (4xxx)
    AUTH_REQUIRED = 4001
    TOKEN_EXPIRED = 4002
    TOKEN_INVALID = 4003
    INSUFFICIENT_PERMISSIONS = 4004

    # Security errors (8xxx)
    SECURITY_VIOLATION = 8001
    INPUT_VALIDATION_FAILED = 8002
    RESOURCE_LIMIT_EXCEEDED = 8003
    UNTRUSTED_CODE_REJECTED = 8004


# CRC32 polynomial for checksum
CRC32_POLYNOMIAL = 0xEDB88320


def calculate_crc32(data: bytes) -> int:
    """Calculate CRC32 checksum matching the algorithm used by all adapters."""
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF
