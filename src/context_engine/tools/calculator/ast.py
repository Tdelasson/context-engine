from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Number:
    value: int


@dataclass(frozen=True)
class UnaryOperation:
    operator: str
    operand: "Expression"


@dataclass(frozen=True)
class BinaryOperation:
    operator: str
    left: "Expression"
    right: "Expression"


Expression = Union[Number, UnaryOperation, BinaryOperation]