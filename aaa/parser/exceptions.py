from aaa import AaaException
from aaa.parser.lib.exceptions import ParserBaseException


class AaaParserBaseException(AaaException):
    def __init__(self, child: ParserBaseException):
        self.child = child

    def __str__(self) -> str:
        return str(self.child)
