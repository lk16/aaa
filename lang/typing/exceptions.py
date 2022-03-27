from typing import Set


class TypeException(Exception):
    ...


class StackUnderflowError(TypeException):
    ...


class FunctionTypeError(TypeException):
    ...


class StackTypesError(TypeException):
    ...


class FunctionNameCollision(TypeException):
    ...


class ArgumentNameCollision(TypeException):
    ...


class UnknownPlaceholderTypes(TypeException):
    def __init__(self, names: Set[str]):
        self.names = names
        # TODO put some message here
