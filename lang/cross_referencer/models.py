from __future__ import annotations

from pathlib import Path
from typing import Dict

from lang.models import AaaModel
from lang.parser import models as parser


class AaaCrossReferenceModel(AaaModel):
    ...


class Unresolved(AaaCrossReferenceModel):
    ...


class Struct(AaaCrossReferenceModel):
    parsed: parser.Struct
    fields: Dict[str, Type | Struct | Unresolved]
    name: str

    def identify(self) -> str:
        return self.name


class Function(AaaCrossReferenceModel):
    parsed: parser.Function
    name: str
    type_name: str
    arguments: Dict[str, Type | Unresolved]
    body: FunctionBody | Unresolved

    def identify(self) -> str:
        if self.type_name:
            return f"{self.type_name}:{self.name}"
        return self.name


class FunctionBody(AaaCrossReferenceModel):
    ...


class Import(AaaCrossReferenceModel):
    parsed: parser.ImportItem
    source_file: Path
    source_name: str
    imported_name: str
    source: Unresolved | Struct | Function

    def identify(self) -> str:
        return self.imported_name


class Type(AaaCrossReferenceModel):
    parsed: parser.TypeLiteral
    name: str
    param_count: int

    def identify(self) -> str:
        return self.name


Function.update_forward_refs()
Struct.update_forward_refs()
