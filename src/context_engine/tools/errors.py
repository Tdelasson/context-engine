"""Explicit deterministic error boundaries for the tool runtime."""


class ToolRuntimeError(Exception):
    """Base exception for deterministic tool runtime failures."""


class DuplicateToolRegistrationError(ToolRuntimeError, ValueError):
    """Raised when attempting to register a tool name more than once."""


class UnknownToolError(ToolRuntimeError, LookupError):
    """Raised when a requested tool is not registered in the registry."""


class ToolInputValidationError(ToolRuntimeError, ValueError):
    """Raised when tool invocation input fails schema validation."""


class ToolPolicyDeniedError(ToolRuntimeError, PermissionError):
    """Raised when tool invocation is denied by deterministic policy."""
