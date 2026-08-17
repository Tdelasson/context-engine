import pytest

from context_engine.tools.calculator.ast import (
    BinaryOperation,
    Number,
    UnaryOperation,
)
from context_engine.tools.calculator.errors import CalculatorParserError
from context_engine.tools.calculator.lexer import CalculatorLexer
from context_engine.tools.calculator.parser import CalculatorParser


@pytest.fixture()
def parser() -> CalculatorParser:
    return CalculatorParser(CalculatorLexer())


def test_parser_parses_number(parser: CalculatorParser) -> None:
    result = parser.parse("42")

    assert result == Number(value=42)


def test_parser_parses_addition(parser: CalculatorParser) -> None:
    result = parser.parse("2 + 3")

    assert result == BinaryOperation(
        operator="+",
        left=Number(value=2),
        right=Number(value=3),
    )


def test_parser_respects_operator_precedence(
    parser: CalculatorParser,
) -> None:
    result = parser.parse("2 + 3 * 4")

    assert result == BinaryOperation(
        operator="+",
        left=Number(value=2),
        right=BinaryOperation(
            operator="*",
            left=Number(value=3),
            right=Number(value=4),
        ),
    )


def test_parser_respects_parentheses(
    parser: CalculatorParser,
) -> None:
    result = parser.parse("(2 + 3) * 4")

    assert result == BinaryOperation(
        operator="*",
        left=BinaryOperation(
            operator="+",
            left=Number(value=2),
            right=Number(value=3),
        ),
        right=Number(value=4),
    )


def test_parser_parses_unary_minus(
    parser: CalculatorParser,
) -> None:
    result = parser.parse("-5")

    assert result == UnaryOperation(
        operator="-",
        operand=Number(value=5),
    )


@pytest.mark.parametrize(
    "expression",
    [
        "2 +",
        "* 2",
        "(2 + 3",
        "2 + 3)",
        "",
    ],
)
def test_parser_rejects_invalid_expression(
    parser: CalculatorParser,
    expression: str,
) -> None:
    with pytest.raises(CalculatorParserError):
        parser.parse(expression)
