from context_engine.tools.calculator.ast import (
    BinaryOperation,
    Expression,
    Number,
    UnaryOperation,
)
from context_engine.tools.calculator.errors import CalculatorEvaluationError


class CalculatorEvaluator:
    def evaluate(self, expression: Expression) -> int:
        if isinstance(expression, Number):
            return expression.value

        if isinstance(expression, UnaryOperation):
            value = self.evaluate(expression.operand)

            if expression.operator == "+":
                return value

            if expression.operator == "-":
                return -value

            raise CalculatorEvaluationError(
                f"Unknown unary operator '{expression.operator}'"
            )

        if isinstance(expression, BinaryOperation):
            left = self.evaluate(expression.left)
            right = self.evaluate(expression.right)

            if expression.operator == "+":
                return left + right

            if expression.operator == "-":
                return left - right

            if expression.operator == "*":
                return left * right

            if expression.operator == "/":
                if right == 0:
                    raise CalculatorEvaluationError("Division by zero")

                return left // right

            raise CalculatorEvaluationError(
                f"Unknown binary operator '{expression.operator}'"
            )

        raise CalculatorEvaluationError(
            f"Unsupported expression node: {type(expression).__name__}"
        )