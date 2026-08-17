import pytest

from context_engine.tools.calculator.errors import CalculatorLexerError
from context_engine.tools.calculator.lexer import (
    CalculatorLexer,
    TokenType,
)


def test_lexer_tokenizes_basic_expression() -> None:
    lexer = CalculatorLexer()

    tokens = lexer.tokenize("2 + 3 * 4")

    assert [token.type for token in tokens] == [
        TokenType.NUMBER,
        TokenType.PLUS,
        TokenType.NUMBER,
        TokenType.MULTIPLY,
        TokenType.NUMBER,
        TokenType.EOF,
    ]

    assert [token.value for token in tokens] == [
        "2",
        "+",
        "3",
        "*",
        "4",
        "",
    ]


def test_lexer_tokenizes_parentheses() -> None:
    lexer = CalculatorLexer()

    tokens = lexer.tokenize("(2 + 3) * 4")

    assert [token.type for token in tokens] == [
        TokenType.LEFT_PAREN,
        TokenType.NUMBER,
        TokenType.PLUS,
        TokenType.NUMBER,
        TokenType.RIGHT_PAREN,
        TokenType.MULTIPLY,
        TokenType.NUMBER,
        TokenType.EOF,
    ]


def test_lexer_ignores_whitespace() -> None:
    lexer = CalculatorLexer()

    tokens = lexer.tokenize("  2   +   3 ")

    assert [token.value for token in tokens] == [
        "2",
        "+",
        "3",
        "",
    ]


def test_lexer_rejects_unsupported_character() -> None:
    lexer = CalculatorLexer()

    with pytest.raises(CalculatorLexerError):
        lexer.tokenize("2 + foo")