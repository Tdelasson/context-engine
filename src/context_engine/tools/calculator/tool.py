from context_engine.tools import (
    Tool,
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
)
from context_engine.tools.calculator.evaluator import CalculatorEvaluator
from context_engine.tools.calculator.lexer import CalculatorLexer
from context_engine.tools.calculator.parser import CalculatorParser


class Calculator(Tool):
    name = "calculator"
    description = "Evaluate a mathematical expression."

    input_schema = ToolInputSchema(
        fields=(
            ToolInputField(
                name="expression",
                value_type=str,
            ),
        )
    )

    def __init__(self) -> None:
        self._parser = CalculatorParser(CalculatorLexer())
        self._evaluator = CalculatorEvaluator()

    def execute(
        self,
        invocation: ToolInvocation,
    ) -> dict[str, object]:
        arguments = invocation.arguments_as_mapping()
        expression = arguments["expression"]

        if not isinstance(expression, str):
            raise RuntimeError("calculator tool received invalid argument types")

        ast = self._parser.parse(expression)
        result = self._evaluator.evaluate(ast)

        return {"value": result}
