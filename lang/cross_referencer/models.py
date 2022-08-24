from __future__ import annotations

from pathlib import Path
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
    name: str

    def identify(self) -> str:
        return self.name


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


class FunctionBody(AaaModel):
    ...


class Import(AaaModel):
    parsed: parser.ImportItem
    source_file: Path
    source_name: str
    imported_name: str
    source: Unresolved | Struct | Function

    def identify(self) -> str:
        return self.imported_name


Function.update_forward_refs()
