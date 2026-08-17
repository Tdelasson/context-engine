import pytest

from context_engine.tools import ToolInvocation
from context_engine.tools.calculator.errors import CalculatorParserError
from context_engine.tools.calculator.tool import Calculator


def test_calculator_tool_returns_result() -> None:
    calculator = Calculator()

    invocation = ToolInvocation.from_mapping(
        tool_name="calculator",
        arguments={
            "expression": "(2 + 3) * 4",
        },
    )

    result = calculator.execute(invocation)

    assert result == {"value": 20}


def test_calculator_tool_rejects_invalid_expression() -> None:
    calculator = Calculator()

    invocation = ToolInvocation.from_mapping(
        tool_name="calculator",
        arguments={
            "expression": "2 +",
        },
    )

    with pytest.raises(CalculatorParserError):
        calculator.execute(invocation)