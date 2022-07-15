class AaaException(Exception):
    def __str__(self) -> str:  # pragma: nocover
        raise NotImplementedError


class AaaLoadException(AaaException):
    ...


class AaaRuntimeException(AaaException):
    ...
