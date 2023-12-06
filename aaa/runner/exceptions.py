from typing import Sequence

from aaa import AaaException


class RunnerBaseException(AaaException):
    ...


class AaaTranslationException(RunnerBaseException):
    """
    Indicates one or more errors happened while reading, parsing, and type-checking Aaa source.
    """

    def __init__(self, exceptions: Sequence[AaaException]) -> None:
        self.exceptions = exceptions


class RustCompilerError(RunnerBaseException):
    ...


class ExcecutableDidNotRun(RunnerBaseException):
    """
    Indidates that excecutable was compiled but did not run.
    The fact it did not run was intentional. This is here to satisfy the type-checker.
    """
