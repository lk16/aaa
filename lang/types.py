

from dataclasses import dataclass
from typing import Dict, Type


class BaseType:
    ...


class Integer(BaseType):
    ...


class Boolean(BaseType):
    ...


class String(BaseType):
    ...


IDENTIFIER_TO_TYPE: Dict[str, Type[BaseType]] = {
    "bool": Boolean,
    "int": Integer,
    "str": String,
}

@dataclass
class ArbitraryType(BaseType):
    name: str
