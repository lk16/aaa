from parser.tokenizer.models import Token
from pathlib import Path
from typing import List

from lang.parse import Function
from lang.typing.signatures import TypeStack


class TypeException(Exception):
    def __init__(self) -> None:
        return super().__init__(self.what())

    def what(self) -> str:
        return "TypeErrorException message, override me!"


class FunctionTypeError(TypeException):
    def __init__(
        self,
        function: Function,
        expected_return_types: TypeStack,
        computed_return_types: TypeStack,
        tokens: List[Token],
        file: Path,
    ) -> None:
        ...

    def what(self) -> str:
        ...


class StackUnderflowError(TypeException):
    ...


class StackTypesError(TypeException):
    ...


class FunctionNameCollision(TypeException):
    ...


class ArgumentNameCollision(TypeException):
    ...


class UnknownFunction(TypeException):
    ...


class UnkonwnType(TypeException):
    ...


class UnknownPlaceholderTypes(TypeException):
    ...
