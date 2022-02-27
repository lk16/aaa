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


class RunTimeError(Exception):
    ...


class UnexpectedType(Exception):
    ...


class UnhandledInstructionError(RunTimeError):
    def __init__(self, instruction: Instruction) -> None:
        super().__init__(f"Unhandled instruction {type(instruction)}")


class StackUnderflow(RunTimeError):
    ...


class InvalidJump(RuntimeError):
    ...


class StackNotEmptyAtExit(RunTimeError):
    ...


class EmptyParseTreeError(Exception):
    ...
