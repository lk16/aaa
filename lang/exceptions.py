from typing import TYPE_CHECKING

from lang.types import Operation

if TYPE_CHECKING:  # pragma: nocover
    from lang.tokenize import Token


class ParseError(Exception):
    ...


class UnhandledTokenType(Exception):
    def __init__(self, token: "Token") -> None:
        super().__init__(f"Unhandled token type: {type(token).__name__}'")


class InvalidBlockStackValue(ParseError):
    def __init__(self, operation: Operation):  # pragma: nocover
        super().__init__(
            f"Invalid block stack value, it has type {type(operation).__name__}"
        )


class UnexpectedToken(ParseError):
    def __init__(self, token: "Token") -> None:
        super().__init__(
            f"Unexpected token {token} on {token.filename}:{token.line_number}:{token.offset + 1}"
        )


class BlockStackNotEmpty(ParseError):
    ...


class UnexpectedEndOfFile(ParseError):
    ...


class NoMainFunctionFound(ParseError):
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


class StackNotEmptyAtExit(RunTimeError):
    ...


class TokenizeError(Exception):
    def __init__(self, filename: str, line_number: int, offset: int, line: str) -> None:
        super().__init__(
            f"Tokenize error on {filename}:{line_number}:{offset + 1}:\n"
            + f"{line}\n"
            + " " * offset
            + "^"
        )


class StringTokenizeError(TokenizeError):
    ...


class UnterminatedStringError(TokenizeError):
    ...


class InvalidStringEscapeSequence(StringTokenizeError):
    ...
