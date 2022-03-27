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


class UnknownFunction(TypeException):
    ...


class UnkonwnType(TypeException):
    ...


class UnknownPlaceholderTypes(TypeException):
    ...
