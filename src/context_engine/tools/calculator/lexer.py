from dataclasses import dataclass
from enum import Enum

from context_engine.tools.calculator.errors import CalculatorLexerError


class TokenType(Enum):
    NUMBER = "number"
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    LEFT_PAREN = "("
    RIGHT_PAREN = ")"
    EOF = "eof"


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    position: int


class CalculatorLexer:
    def tokenize(self, expression: str) -> list[Token]:
        tokens: list[Token] = []
        position = 0

        while position < len(expression):
            character = expression[position]

            if character.isspace():
                position += 1
                continue

            if character.isdigit() or (
                character == "."
                and position + 1 < len(expression)
                and expression[position + 1].isdigit()
            ):
                start = position
                seen_decimal = character == "."

                position += 1

                while position < len(expression):
                    current = expression[position]

                    if current.isdigit():
                        position += 1
                        continue

                    if current == "." and not seen_decimal:
                        seen_decimal = True
                        position += 1
                        continue

                    break

                tokens.append(
                    Token(
                        type=TokenType.NUMBER,
                        value=expression[start:position],
                        position=start,
                    )
                )
                continue

            token_types = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.MULTIPLY,
                "/": TokenType.DIVIDE,
                "(": TokenType.LEFT_PAREN,
                ")": TokenType.RIGHT_PAREN,
            }

            token_type = token_types.get(character)

            if token_type is None:
                raise CalculatorLexerError(
                    f"Unexpected character '{character}' at position {position}"
                )

            tokens.append(
                Token(
                    type=token_type,
                    value=character,
                    position=position,
                )
            )

            position += 1

        tokens.append(
            Token(
                type=TokenType.EOF,
                value="",
                position=position,
            )
        )

        return tokens
