from lang.operations import Operation


class ParseError(Exception):
    ...


class SyntaxException(Exception):
    def __init__(self, word: str) -> None:
        super().__init__(f"Parse error: can't handle '{word}'")


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
