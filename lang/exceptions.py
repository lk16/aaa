from lang.operations import Operation
from lang.tokenize import Token


class ParseError(Exception):
    ...


class UnhandledTokenType(Exception):
    def __init__(self, token: Token) -> None:
        super().__init__(f"Unhandled token type: {type(token).__name__}'")


class InvalidBlockStackValue(ParseError):
    def __init__(self, operation: Operation):  # pragma: nocover
        super().__init__(
            f"Invalid block stack value, it has type {type(operation).__name__}"
        )


class BlockStackNotEmpty(ParseError):
    ...


class RunTimeError(Exception):
    ...


class UnexpectedType(Exception):
    ...


class UnhandledOperationError(RunTimeError):
    def __init__(self, operation: Operation) -> None:
        super().__init__(f"Unhandled operation {type(operation)}")


class StackUnderflow(RunTimeError):
    ...


class InvalidJump(RuntimeError):
    ...


class UnexpectedOperation(RunTimeError):
    def __init__(self, operation: Operation) -> None:
        super().__init__(f"Unexpected operation {type(operation)}")


class StackNotEmptyAtExit(RunTimeError):
    ...


class TokenizeError(Exception):
    def __init__(self, filename: str, line_number: int, offset: int, line: str) -> None:
        msg = f"Tokenize error on {filename}:{line_number}:{offset}:\n{line}\n"
        msg += " " * offset
        msg += "^"
        super().__init__(msg)
