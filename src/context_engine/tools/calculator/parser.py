from context_engine.tools.calculator.ast import (
    BinaryOperation,
    Expression,
    Number,
    UnaryOperation,
)
from context_engine.tools.calculator.errors import CalculatorParserError
from context_engine.tools.calculator.lexer import (
    CalculatorLexer,
    Token,
    TokenType,
)


class ParserCursor:

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._position = 0

    def _advance(self) -> Token:
            token = self._current()
            self._position += 1
            return token

    def _current(self) -> int:
        return self._tokens[self._position]

class CalculatorParser:
    def __init__(self, lexer: CalculatorLexer) -> None:
        self._lexer = lexer
        self._tokens: list[Token] = []
        self._position = 0

    def parse(self, expression: str) -> Expression:
        self._tokens = self._lexer.tokenize(expression)

        self._parserCursor: ParserCursor = ParserCursor(self._tokens)

        self._position = 0

        result = self._parse_expression()

        if self._current().type is not TokenType.EOF:
            raise CalculatorParserError(
                f"Unexpected token '{self._current().value}'"
            )

        return result

    def _parse_expression(self) -> Expression:
        left = self._parse_term()

        while self._current().type in (
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            operator = self._advance().value
            right = self._parse_term()

            left = BinaryOperation(
                operator=operator,
                left=left,
                right=right,
            )

        return left

    def _parse_term(self) -> Expression:
        left = self._parse_unary()

        while self._current().type in (
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
        ):
            operator = self._advance().value
            right = self._parse_unary()

            left = BinaryOperation(
                operator=operator,
                left=left,
                right=right,
            )

        return left

    def _parse_unary(self) -> Expression:
        if self._current().type in (
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            operator = self._advance().value

            return UnaryOperation(
                operator=operator,
                operand=self._parse_unary(),
            )

        return self._parse_primary()

    def _parse_primary(self) -> Expression:
        token = self._current()

        if token.type is TokenType.NUMBER:
            self._advance()

            return Number(
                value=int(token.value),
            )

        if token.type is TokenType.LEFT_PAREN:
            self._advance()

            expression = self._parse_expression()

            if self._current().type is not TokenType.RIGHT_PAREN:
                raise CalculatorParserError("Expected ')'")

            self._advance()

            return expression

        raise CalculatorParserError(
            f"Expected number or '(' but got '{token.value}'"
        )

    def _current(self) -> Token:
        return self._parserCursor._current()
