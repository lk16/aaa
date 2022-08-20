from __future__ import annotations

from typing import Dict, List

from lang.models import AaaModel
from lang.parser import models as parser


class AaaCrossReferenceModel(AaaModel):
    ...


class Unresolved(AaaModel):
    ...


class Type(AaaModel):
    parsed: parser.TypeLiteral | parser.TypePlaceholder
    name: str
    is_placeholder: bool
    params: List["Type"]


class Struct(AaaModel):
    parsed: parser.Struct
    fields: Dict[str, Type | Unresolved]


class Function(AaaModel):
    parsed: parser.Function
    name: str
    type_name: str
    arguments: Dict[str, Type | Unresolved]
    body: FunctionBody | Unresolved

    def identify(self) -> str:
        if self.type_name:
            return f"{self.type_name}:{self.name}"
        return self.name


class FunctionBody:
    ...


Function.update_forward_refs()
