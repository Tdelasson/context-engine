"""Calculator-specific exceptions for deterministic error handling."""


class CalculatorError(ValueError):
    """Base exception for calculator operations."""


class CalculatorLexerError(CalculatorError):
    """Raised when the lexer encounters an invalid token or character."""


class CalculatorParserError(CalculatorError):
    """Raised when the parser encounters invalid syntax."""


class CalculatorEvaluationError(CalculatorError):
    """Raised when evaluation fails (division by zero, invalid expressions, etc)."""
