from lang.operations import Operation


class ParseError(Exception):
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
