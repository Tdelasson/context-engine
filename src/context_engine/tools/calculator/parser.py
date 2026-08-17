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

    def advance(self) -> Token:
        token = self.current()
        self._position += 1
        return token

    def current(self) -> Token:
        return self._tokens[self._position]


class CalculatorParser:
    def __init__(self, lexer: CalculatorLexer) -> None:
        self._lexer = lexer

    def parse(self, expression: str) -> Expression:
        cursor = ParserCursor(self._lexer.tokenize(expression))
        result = self._parse_expression(cursor)

        if cursor.current().type is not TokenType.EOF:
            raise CalculatorParserError(f"Unexpected token '{cursor.current().value}'")

        return result

    def _parse_expression(self, cursor: ParserCursor) -> Expression:
        left = self._parse_term(cursor)

        while cursor.current().type in (
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            operator = cursor.advance().value
            right = self._parse_term(cursor)

            left = BinaryOperation(
                operator=operator,
                left=left,
                right=right,
            )

        return left

    def _parse_term(self, cursor: ParserCursor) -> Expression:
        left = self._parse_unary(cursor)

        while cursor.current().type in (
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
        ):
            operator = cursor.advance().value
            right = self._parse_unary(cursor)

            left = BinaryOperation(
                operator=operator,
                left=left,
                right=right,
            )

        return left

    def _parse_unary(self, cursor: ParserCursor) -> Expression:
        if cursor.current().type in (
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            operator = cursor.advance().value

            return UnaryOperation(
                operator=operator,
                operand=self._parse_unary(cursor),
            )

        return self._parse_primary(cursor)

    def _parse_primary(self, cursor: ParserCursor) -> Expression:
        token = cursor.current()

        if token.type is TokenType.NUMBER:
            cursor.advance()

            return Number(
                value=float(token.value) if "." in token.value else int(token.value),
            )

        if token.type is TokenType.LEFT_PAREN:
            cursor.advance()

            expression = self._parse_expression(cursor)

            if cursor.current().type is not TokenType.RIGHT_PAREN:
                raise CalculatorParserError("Expected ')'")

            cursor.advance()

            return expression

        raise CalculatorParserError(f"Expected number or '(' but got '{token.value}'")
