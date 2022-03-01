from typing import List

from lang.instruction_types import Instruction


class ParseError(Exception):
    ...


class InvalidBlockStackValue(ParseError):
    def __init__(self, instruction: Instruction):  # pragma: nocover
        super().__init__(
            f"Invalid block stack value, it has type {type(instruction).__name__}"
        )


class BlockStackNotEmpty(ParseError):
    ...


class UnexpectedEndOfFile(ParseError):
    ...


class NoMainFunctionFound(ParseError):
    ...


class FunctionNameCollission(ParseError):
    def __init__(self, func_name: str) -> None:
        super().__init__(f"Function with name {func_name} was already defined earlier.")


class InvalidFunctionArgumentList(ParseError):
    def __init__(self, func_name: str, arguments: List[str]) -> None:
        super().__init__(
            f"Function name and/or arguments overlap: {func_name} "
            + " ".join(arguments)
        )


class RunTimeError(Exception):
    ...


class UnexpectedType(Exception):
    ...


class StackUnderflow(RunTimeError):
    ...


class InvalidJump(RuntimeError):
    ...


class StackNotEmptyAtExit(RunTimeError):
    ...


class EmptyParseTreeError(Exception):
    ...


class InvalidFunctionCall(RunTimeError):
    def __init__(self, func_name: str, offset: int, invalid_func: str):
        super().__init__(
            f"Call to non-existent function {invalid_func} in {func_name} at offset {offset}"
        )
