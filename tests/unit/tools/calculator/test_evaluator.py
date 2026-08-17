import pytest

from context_engine.tools.calculator.errors import CalculatorEvaluationError
from context_engine.tools.calculator.evaluator import CalculatorEvaluator
from context_engine.tools.calculator.parser import CalculatorParser
from context_engine.tools.calculator.lexer import CalculatorLexer

@pytest.fixture
def evaluate():
    parser = CalculatorParser(CalculatorLexer())
    evaluator = CalculatorEvaluator()

    def _evaluate(expression: str) -> int:
        ast = parser.parse(expression)
        return evaluator.evaluate(ast)

    return _evaluate


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2", 2),
        ("2 + 3", 5),
        ("10 - 3", 7),
        ("2 * 4", 8),
        ("10 / 2", 5),
        ("2 + 3 * 4", 14),
        ("(2 + 3) * 4", 20),
        ("10 - 2 * 3", 4),
        ("-5", -5),
        ("-5 + 10", 5),
        ("2 * -3", -6),
    ],
)
def test_evaluator(
    evaluate,
    expression: str,
    expected: int,
) -> None:
    assert evaluate(expression) == expected


def test_evaluator_rejects_division_by_zero(evaluate) -> None:
    with pytest.raises(CalculatorEvaluationError, match="Division by zero"):
        evaluate("10 / 0")