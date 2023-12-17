from __future__ import annotations

import os
from pathlib import Path

from basil.models import Position, Token

from aaa import AaaModel


class AaaParseModel(AaaModel):
    def __init__(self, position: Position) -> None:
        self.position = position

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> AaaParseModel:
        raise NotImplementedError(f"for {cls.__name__}")


class Integer(AaaParseModel):
    def __init__(self, position: Position, value: int) -> None:
        self.value = value
        super().__init__(position)


class String(AaaParseModel):
    def __init__(self, position: Position, value: str) -> None:
        self.value = value
        super().__init__(position)


class Boolean(AaaParseModel):
    def __init__(self, position: Position, value: bool) -> None:
        self.value = value
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Boolean:
        assert len(children) == 1
        child = children[0]
        assert isinstance(child, Token)
        return Boolean(child.position, child.value == "true")


class Char(AaaParseModel):
    def __init__(self, position: Position, value: str) -> None:
        self.value = value
        super().__init__(position)


class WhileLoop(AaaParseModel):
    def __init__(
        self,
        position: Position,
        condition: FunctionBody,
        body: FunctionBodyBlock,
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> WhileLoop:
        assert len(children) == 3
        while_token, condition, body_block = children
        assert isinstance(while_token, Token)
        assert isinstance(condition, FunctionBody)
        assert isinstance(body_block, FunctionBodyBlock)

        return WhileLoop(while_token.position, condition, body_block)


class Identifier(AaaParseModel):
    def __init__(self, position: Position, name: str) -> None:
        self.value = name
        super().__init__(position)


class Branch(AaaParseModel):
    def __init__(
        self,
        position: Position,
        condition: FunctionBody,
        if_body_block: FunctionBodyBlock,
        else_body_block: FunctionBodyBlock | None,
    ) -> None:
        self.condition = condition
        self.if_body_block = if_body_block
        self.else_body_block = else_body_block
        super().__init__(position)

    def get_if_body(self) -> FunctionBody:
        return self.if_body_block.value

    def get_else_body(self) -> FunctionBody | None:
        block = self.else_body_block
        if block:
            return block.value
        return None

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Branch:
        assert len(children) in [3, 5]

        if_token, condition, if_body_block = children[:3]
        assert isinstance(if_token, Token)
        assert isinstance(condition, FunctionBody)
        assert isinstance(if_body_block, FunctionBodyBlock)

        if len(children) == 5:
            else_body_block = children[4]
            assert isinstance(else_body_block, FunctionBodyBlock)
        else:
            else_body_block = None

        return Branch(if_token.position, condition, if_body_block, else_body_block)


class FunctionBody(AaaParseModel):
    def __init__(self, position: Position, items: list[FunctionBodyItem]) -> None:
        self.items = [item.value for item in items]
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FunctionBody:
        items: list[FunctionBodyItem] = []

        for child in children:
            assert isinstance(child, FunctionBodyItem)
            items.append(child)

        return FunctionBody(children[0].position, items)


class StructFieldQuery(AaaParseModel):
    def __init__(self, field_name: String, operator_position: Position) -> None:
        self.field_name = field_name
        self.operator_position = operator_position
        super().__init__(field_name.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> StructFieldQuery:
        assert len(children) == 2
        field_name, get_field_token = children
        assert isinstance(field_name, String)
        assert isinstance(get_field_token, Token)

        return StructFieldQuery(field_name, get_field_token.position)


class StructFieldUpdate(AaaParseModel):
    def __init__(
        self,
        field_name: String,
        new_value_block: FunctionBodyBlock,
        operator_position: Position,
    ) -> None:
        self.field_name = field_name
        self.new_value_expr = new_value_block
        self.operator_position = operator_position
        super().__init__(field_name.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> StructFieldUpdate:
        assert len(children) == 3
        field_name, new_value_block, set_field_token = children
        assert isinstance(field_name, String)
        assert isinstance(new_value_block, FunctionBodyBlock)
        assert isinstance(set_field_token, Token)

        return StructFieldUpdate(field_name, new_value_block, set_field_token.position)


class GetFunctionPointer(AaaParseModel):
    def __init__(self, position: Position, function_name: String):
        self.function_name = function_name
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> GetFunctionPointer:
        function_name = children[0]
        assert isinstance(function_name, String)

        return GetFunctionPointer(function_name.position, function_name)


class Return(AaaParseModel):
    ...


class Call(AaaParseModel):
    ...


class Argument(AaaParseModel):
    def __init__(
        self, identifier: Identifier, type: TypeOrFunctionPointerLiteral
    ) -> None:
        self.identifier = identifier
        self.type = type
        super().__init__(identifier.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Argument:
        assert len(children) == 3
        identifier, _, type_or_func_ptr_literal = children

        assert isinstance(identifier, Identifier)
        assert isinstance(type_or_func_ptr_literal, TypeOrFunctionPointerLiteral)

        return Argument(identifier, type_or_func_ptr_literal)


class Function(AaaParseModel):
    def __init__(
        self,
        is_builtin: bool,
        declaration: FunctionDeclaration,
        body_block: FunctionBodyBlock | None,
    ) -> None:
        self.is_builtin = is_builtin
        self.declaration = declaration
        self.body_block = body_block
        super().__init__(declaration.position)

    def is_test(self) -> bool:  # pragma: nocover
        return not self.get_type_name() and self.get_func_name().startswith("test_")

    def get_params(self) -> list[Identifier]:
        return self.declaration.name.get_params()

    def get_func_name(self) -> str:
        return self.declaration.name.get_func_name()

    def get_type_name(self) -> str:
        return self.declaration.name.get_type_name()

    def get_name(self) -> str:
        type_name = self.get_type_name()
        func_name = self.get_func_name()
        if type_name:
            return f"{type_name}:{func_name}"
        return func_name

    def get_end_position(self) -> Position | None:
        if not self.body_block:
            return None
        return self.body_block.end_token_position

    def get_body(self) -> FunctionBody | None:
        if not self.body_block:
            return None
        return self.body_block.value

    def get_arguments(self) -> list[Argument]:
        arguments = self.declaration.arguments
        if not arguments:
            return []
        return arguments.value

    def get_return_types(
        self,
    ) -> list[TypeLiteral | FunctionPointerTypeLiteral] | Never:
        return_types = self.declaration.return_types
        if not return_types:
            return []
        if isinstance(return_types.value, Never):
            return return_types.value
        return [item.literal for item in return_types.value]

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Function:
        assert len(children) == 2

        if isinstance(children[0], Token):
            assert children[0].type == "builtin"

            declaration = children[1]
            assert isinstance(declaration, FunctionDeclaration)
            return Function(True, declaration, None)

        declaration = children[0]
        assert isinstance(declaration, FunctionDeclaration)

        body_block = children[1]
        assert isinstance(body_block, FunctionBodyBlock)

        return Function(False, declaration, body_block)


class ImportItem(AaaParseModel):
    def __init__(self, original: Identifier, imported: Identifier) -> None:
        self.original = original
        self.imported = imported
        super().__init__(original.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> ImportItem:
        original = children[0]
        assert isinstance(original, Identifier)

        if len(children) == 3:
            imported = children[2]
            assert isinstance(imported, Identifier)
        else:
            imported = original

        return ImportItem(original, imported)


class ImportItems(AaaParseModel):
    def __init__(self, items: list[ImportItem]) -> None:
        assert len(items) >= 1

        self.value = items
        super().__init__(items[0].position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> ImportItems:
        items: list[ImportItem] = []

        for child in children:
            if isinstance(child, ImportItem):
                items.append(child)
            elif isinstance(child, Token):
                pass  # ignore token
            else:
                raise NotImplementedError

        return ImportItems(items)


class Import(AaaParseModel):
    def __init__(
        self, position: Position, source: String, imported_items: ImportItems
    ) -> None:
        self.source = source
        self.imported_items = imported_items
        super().__init__(position)

    def get_source_file(self) -> Path:
        source_path = Path(self.source.value)

        if source_path.is_file() and self.source.value.endswith(".aaa"):
            return source_path
        else:
            return self.position.file.parent / (
                self.source.value.replace(".", os.sep) + ".aaa"
            )

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Import:
        assert len(children) == 4
        from_token, source, _, import_items = children
        assert isinstance(from_token, Token)
        assert isinstance(source, String)
        assert isinstance(import_items, ImportItems)

        return Import(from_token.position, source, import_items)


class Struct(AaaParseModel):
    def __init__(
        self,
        is_builtin: bool,
        declaration: StructDeclaration,
        fields: StructFields | None,
    ) -> None:
        self.is_builtin = is_builtin
        self.declaration = declaration
        self.fields = fields
        super().__init__(declaration.position)

    def get_name(self) -> str:
        return self.declaration.flat_type_literal.identifier.value

    def get_params(self) -> list[Identifier]:
        return self.declaration.flat_type_literal.params

    def get_fields(
        self,
    ) -> dict[str, TypeLiteral | FunctionPointerTypeLiteral] | None:
        if self.is_builtin:
            return None

        if not self.fields:
            return {}

        return {field.name.value: field.type.literal for field in self.fields.value}

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Struct:
        if isinstance(children[0], Token):
            assert len(children) == 2

            assert children[0].type == "builtin"

            declaration = children[1]
            assert isinstance(declaration, StructDeclaration)

            return Struct(True, declaration, None)

        declaration = children[0]
        assert isinstance(declaration, StructDeclaration)

        fields: StructFields | None = None
        if isinstance(children[2], StructFields):
            fields = children[2]

        return Struct(False, declaration, fields)


class StructDeclaration(AaaParseModel):
    def __init__(self, position: Position, flat_type_literal: FlatTypeLiteral) -> None:
        self.flat_type_literal = flat_type_literal
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> StructDeclaration:
        assert len(children) == 2

        struct_token, flat_type_literal = children
        assert isinstance(struct_token, Token)
        assert isinstance(flat_type_literal, FlatTypeLiteral)

        return StructDeclaration(struct_token.position, flat_type_literal)


class SourceFile(AaaParseModel):
    def __init__(
        self,
        position: Position,
        functions: list[Function],
        imports: list[Import],
        structs: list[Struct],
        enums: list[Enum],
    ) -> None:
        self.functions = functions
        self.imports = imports
        self.structs = structs
        self.enums = enums
        super().__init__(position)

    def get_dependencies(self) -> set[Path]:
        return {import_.get_source_file() for import_ in self.imports}

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> SourceFile:
        if children:
            file = children[0].position.file
        else:
            file = Path("/dev/unknown")

        position = Position(file, 1, 1)
        functions: list[Function] = []
        imports: list[Import] = []
        structs: list[Struct] = []
        enums: list[Enum] = []

        for child in children:
            if isinstance(child, Function):
                functions.append(child)
            elif isinstance(child, Import):
                imports.append(child)
            elif isinstance(child, Struct):
                structs.append(child)
            elif isinstance(child, Enum):
                enums.append(child)
            else:
                raise NotImplementedError

        return SourceFile(position, functions, imports, structs, enums)


class EnumDeclaration(AaaParseModel):
    def __init__(self, position: Position, name: Identifier) -> None:
        self.name = name
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> EnumDeclaration:
        assert len(children) == 2
        enum_token, name = children

        assert isinstance(enum_token, Token)
        assert isinstance(name, Identifier)
        return EnumDeclaration(enum_token.position, name)


class FlatTypeParams(AaaParseModel):
    def __init__(self, position: Position, type_params: list[Identifier]) -> None:
        self.value = type_params
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FlatTypeParams:
        sq_start_token = children[0]
        type_params: list[Identifier] = []

        for child in children[1:]:
            if isinstance(child, Identifier):
                type_params.append(child)
            elif isinstance(child, Token):
                pass  # Ignore sq brackets and comma
            else:
                raise NotImplementedError  # Unexpected other model

        return FlatTypeParams(sq_start_token.position, type_params)


class TypeLiteral(AaaParseModel):
    def __init__(
        self,
        position: Position,
        identifier: Identifier,
        params: list[TypeOrFunctionPointerLiteral],
        const: bool,
    ) -> None:
        self.identifier = identifier
        self.params = params
        self.const = const
        super().__init__(position)

    def get_params(self) -> list[TypeLiteral | FunctionPointerTypeLiteral]:
        return [item.literal for item in self.params]

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> TypeLiteral:
        assert len(children) <= 3

        const = False
        identifier: Identifier | None = None
        params: list[TypeOrFunctionPointerLiteral] = []

        for child in children:
            if isinstance(child, Token):
                if child.type == "const":
                    const = True
                else:
                    raise NotImplementedError

            elif isinstance(child, Identifier):
                identifier = child

            elif isinstance(child, TypeParams):
                params = child.value

        assert identifier  # required by parser

        return TypeLiteral(children[0].position, identifier, params, const)


class StructField(AaaParseModel):
    def __init__(self, name: Identifier, type: TypeOrFunctionPointerLiteral):
        self.name = name
        self.type = type
        super().__init__(name.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> StructField:
        assert len(children) == 3
        name, _, type = children
        assert isinstance(name, Identifier)
        assert isinstance(type, TypeOrFunctionPointerLiteral)

        return StructField(name, type)


class StructFields(AaaParseModel):
    def __init__(self, fields: list[StructField]) -> None:
        assert len(fields) >= 1

        self.value = fields
        super().__init__(fields[0].position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> StructFields:
        fields: list[StructField] = []

        for child in children:
            if isinstance(child, StructField):
                fields.append(child)
            elif isinstance(child, Token):
                pass  # ignore commas
            else:
                raise NotImplementedError

        return StructFields(fields)


class FlatTypeLiteral(AaaParseModel):
    def __init__(
        self,
        position: Position,
        identifier: Identifier,
        params: list[Identifier],
    ) -> None:
        self.identifier = identifier
        self.params = params
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FlatTypeLiteral:
        assert len(children) <= 2

        identifier = children[0]
        assert isinstance(identifier, Identifier)

        params: list[Identifier] = []
        if len(children) == 2:
            flat_type_params = children[1]
            assert isinstance(flat_type_params, FlatTypeParams)
            params = flat_type_params.value

        return FlatTypeLiteral(identifier.position, identifier, params)


class FunctionPointerTypeLiteral(AaaParseModel):
    def __init__(
        self,
        position: Position,
        argument_types: CommaSeparatedTypeList | None,
        return_types: CommaSeparatedTypeList | Never | None,
    ) -> None:
        self.argument_types = argument_types
        self.return_types = return_types
        super().__init__(position)

    def get_arguments(self) -> list[TypeLiteral | FunctionPointerTypeLiteral]:
        if self.argument_types is None:
            return []
        return [item.literal for item in self.argument_types.value]

    def get_return_types(
        self,
    ) -> list[TypeLiteral | FunctionPointerTypeLiteral] | Never:
        if self.return_types is None:
            return []
        if isinstance(self.return_types, Never):
            return self.return_types
        return [item.literal for item in self.return_types.value]

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FunctionPointerTypeLiteral:
        fn_token = children[0]
        assert isinstance(fn_token, Token)

        if isinstance(children[2], CommaSeparatedTypeList):
            arg_list = children[2]
        else:
            arg_list = None

        return_type_list: CommaSeparatedTypeList | Never | None = None

        for child in children[4:]:
            if isinstance(child, Token) and child.value == "never":
                return_type_list = Never(child.position)
                break

            if isinstance(child, CommaSeparatedTypeList):
                return_type_list = child
                break

        return FunctionPointerTypeLiteral(fn_token.position, arg_list, return_type_list)


class CommaSeparatedTypeList(AaaParseModel):
    def __init__(self, literals: list[TypeOrFunctionPointerLiteral]) -> None:
        assert len(literals) >= 1

        self.value = literals
        super().__init__(literals[0].position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> CommaSeparatedTypeList:
        literals: list[TypeOrFunctionPointerLiteral] = []

        for child in children:
            if isinstance(child, TypeOrFunctionPointerLiteral):
                literals.append(child)
            elif isinstance(child, Token):
                pass  # ignore commas
            else:
                raise NotImplementedError

        return CommaSeparatedTypeList(literals)


class FunctionName(AaaParseModel):
    def __init__(self, name: FreeFunctionName | MemberFunctionName) -> None:
        self.name = name
        super().__init__(name.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FunctionName:
        name = children[0]
        assert isinstance(name, FreeFunctionName | MemberFunctionName)

        return FunctionName(name)

    def get_params(self) -> list[Identifier]:
        return self.name.get_params()

    def get_func_name(self) -> str:
        return self.name.get_func_name()

    def get_type_name(self) -> str:
        return self.name.get_type_name()


class FunctionDeclaration(AaaParseModel):
    def __init__(
        self,
        position: Position,
        name: FunctionName,
        arguments: Arguments | None,
        return_types: ReturnTypes | None,
    ) -> None:
        self.name = name
        self.arguments = arguments
        self.return_types = return_types
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FunctionDeclaration:
        fn_token = children[0]
        assert isinstance(fn_token, Token)

        name = children[1]
        assert isinstance(name, FunctionName)

        arguments: Arguments | None = None
        return_types: ReturnTypes | None = None

        for child in children[2:]:
            if isinstance(child, Arguments):
                arguments = child
            elif isinstance(child, ReturnTypes):
                return_types = child
            elif isinstance(child, Token | Return):
                pass
            else:
                raise NotImplementedError  # Unexpected child

        return FunctionDeclaration(fn_token.position, name, arguments, return_types)


class Arguments(AaaParseModel):
    def __init__(self, position: Position, arguments: list[Argument]) -> None:
        assert len(arguments) >= 1

        self.value = arguments
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Arguments:
        arg_token = children[0]
        assert isinstance(arg_token, Token)

        arguments: list[Argument] = []

        for child in children[1:]:
            if isinstance(child, Argument):
                arguments.append(child)
            elif isinstance(child, Token):
                pass  # ignore commas
            else:
                raise NotImplementedError

        return Arguments(arg_token.position, arguments)


class ReturnTypes(AaaParseModel):
    def __init__(
        self,
        position: Position,
        return_types: list[TypeOrFunctionPointerLiteral] | Never,
    ) -> None:
        self.value = return_types
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> ReturnTypes:
        return_token = children[0]
        assert isinstance(return_token, Return)

        return_types: list[TypeOrFunctionPointerLiteral] | Never

        if isinstance(children[1], Token) and children[1].value == "never":
            return_types = Never(children[1].position)

        else:
            return_types = []

            for child in children[1:]:
                if isinstance(child, TypeOrFunctionPointerLiteral):
                    return_types.append(child)
                elif isinstance(child, Token):
                    pass  # Ignore commas
                else:
                    raise NotImplementedError

        return ReturnTypes(return_token.position, return_types)


class TypeOrFunctionPointerLiteral(AaaParseModel):
    def __init__(self, literal: TypeLiteral | FunctionPointerTypeLiteral) -> None:
        self.literal = literal
        super().__init__(literal.position)

    @classmethod
    def load(
        cls, children: list[AaaParseModel | Token]
    ) -> TypeOrFunctionPointerLiteral:
        assert len(children) == 1
        child = children[0]

        assert isinstance(child, TypeLiteral | FunctionPointerTypeLiteral)
        return TypeOrFunctionPointerLiteral(child)


class FreeFunctionCall(AaaParseModel):
    def __init__(self, func_name: Identifier, params: TypeParams | None) -> None:
        self.func_name = func_name
        self.params = params
        super().__init__(func_name.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FreeFunctionCall:
        func_name = children[0]
        assert isinstance(func_name, Identifier)

        if len(children) > 1:
            params = children[1]
            assert isinstance(params, TypeParams)
        else:
            params = None

        return FreeFunctionCall(func_name, params)

    def name(self) -> str:
        return self.func_name.value

    def get_type_params(
        self,
    ) -> list[TypeLiteral | FunctionPointerTypeLiteral]:
        if not self.params:
            return []
        return [item.literal for item in self.params.value]


class MemberFunctionCall(AaaParseModel):
    def __init__(
        self,
        type_name: Identifier,
        func_name: Identifier,
        params: TypeParams | None,
    ) -> None:
        self.type_name = type_name
        self.func_name = func_name
        self.params = params
        super().__init__(func_name.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> MemberFunctionCall:
        type_name = children[0]
        assert isinstance(type_name, Identifier)

        func_name = children[2]
        assert isinstance(func_name, Identifier)

        if len(children) > 3:
            params = children[3]
            assert isinstance(params, TypeParams)
        else:
            params = None

        return MemberFunctionCall(type_name, func_name, params)

    def name(self) -> str:
        return f"{self.type_name.value}:{self.func_name.value}"

    def get_type_params(
        self,
    ) -> list[TypeLiteral | FunctionPointerTypeLiteral]:
        if not self.params:
            return []
        return [item.literal for item in self.params.value]


class FreeFunctionName(AaaParseModel):
    def __init__(self, func_name: Identifier, params: FlatTypeParams | None) -> None:
        self.func_name = func_name
        self.params = params
        super().__init__(func_name.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FreeFunctionName:
        func_name = children[0]
        assert isinstance(func_name, Identifier)

        if len(children) > 1:
            params = children[1]
            assert isinstance(params, FlatTypeParams)
        else:
            params = None

        return FreeFunctionName(func_name, params)

    def get_params(self) -> list[Identifier]:
        if not self.params:
            return []
        return self.params.value

    def get_func_name(self) -> str:
        return self.func_name.value

    def get_type_name(self) -> str:
        return ""


class MemberFunctionName(AaaParseModel):
    def __init__(
        self,
        type_name: Identifier,
        params: FlatTypeParams | None,
        func_name: Identifier,
    ) -> None:
        self.type_name = type_name
        self.params = params
        self.func_name = func_name
        super().__init__(type_name.position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> MemberFunctionName:
        type_name = children[0]
        assert isinstance(type_name, Identifier)

        if isinstance(children[1], FlatTypeParams):
            params = children[1]
        else:
            params = None

        func_name = children[-1]
        assert isinstance(func_name, Identifier)

        return MemberFunctionName(type_name, params, func_name)

    def get_params(self) -> list[Identifier]:
        if not self.params:
            return []
        return self.params.value

    def get_func_name(self) -> str:
        return self.func_name.value

    def get_type_name(self) -> str:
        return self.type_name.value


class FunctionCall(AaaParseModel):
    def __init__(self, call: FreeFunctionCall | MemberFunctionCall) -> None:
        self.call = call
        super().__init__(call.position)

    def name(self) -> str:
        return self.call.name()

    def get_type_params(
        self,
    ) -> list[TypeLiteral | FunctionPointerTypeLiteral]:
        return self.call.get_type_params()

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FunctionCall:
        call = children[0]
        assert isinstance(call, FreeFunctionCall | MemberFunctionCall)

        return FunctionCall(call)


class TypeParams(AaaParseModel):
    def __init__(self, value: list[TypeOrFunctionPointerLiteral]) -> None:
        assert len(value) >= 1

        self.value = value
        super().__init__(value[0].position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> TypeParams:
        type_params: list[TypeOrFunctionPointerLiteral] = []

        for child in children:
            if isinstance(child, TypeOrFunctionPointerLiteral):
                type_params.append(child)
            elif isinstance(child, Token):
                pass  # Ignore square brackets and commas
            else:
                raise NotImplementedError

        return TypeParams(type_params)


class Variables(AaaParseModel):
    def __init__(self, value: list[Identifier]) -> None:
        assert len(value) >= 1

        self.value = value
        super().__init__(value[0].position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Variables:
        variables: list[Identifier] = []

        for child in children:
            if isinstance(child, Identifier):
                variables.append(child)
            elif isinstance(child, Token):
                pass  # Ignore square brackets and commas
            else:
                raise NotImplementedError

        return Variables(variables)


class CaseLabel(AaaParseModel):
    def __init__(
        self,
        position: Position,
        enum_name: Identifier,
        variant_name: Identifier,
        variables: Variables | None,
    ) -> None:
        self.enum_name = enum_name
        self.variant_name = variant_name
        self.variables = variables
        super().__init__(position)

    def get_variables(self) -> list[Identifier]:
        if not self.variables:
            return []
        return self.variables.value

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> CaseLabel:
        enum_name, _, variant_name = children[:3]
        assert isinstance(enum_name, Identifier)
        assert isinstance(variant_name, Identifier)

        if len(children) > 3:
            variables = children[4]
            assert isinstance(variables, Variables)
        else:
            variables = None

        return CaseLabel(enum_name.position, enum_name, variant_name, variables)


class ForeachLoop(AaaParseModel):
    def __init__(self, position: Position, body_block: FunctionBodyBlock) -> None:
        self.body = body_block
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> ForeachLoop:
        assert len(children) == 2
        foreach_token, body_block = children
        assert isinstance(foreach_token, Token)
        assert isinstance(body_block, FunctionBodyBlock)

        return ForeachLoop(foreach_token.position, body_block)


class UseBlock(AaaParseModel):
    def __init__(
        self,
        position: Position,
        variables: Variables,
        body_block: FunctionBodyBlock,
    ) -> None:
        self.variables = variables
        self.body_block = body_block
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> UseBlock:
        assert len(children) == 3
        use_token, variables, body_block = children
        assert isinstance(use_token, Token)
        assert isinstance(variables, Variables)
        assert isinstance(body_block, FunctionBodyBlock)

        return UseBlock(use_token.position, variables, body_block)


class Assignment(AaaParseModel):
    def __init__(
        self,
        position: Position,
        variables: Variables,
        body_block: FunctionBodyBlock,
    ) -> None:
        self.variables = variables
        self.body_block = body_block
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Assignment:
        assert len(children) == 3
        variables, _, body_block = children
        assert isinstance(variables, Variables)
        assert isinstance(body_block, FunctionBodyBlock)

        return Assignment(variables.position, variables, body_block)


class CaseBlock(AaaParseModel):
    def __init__(
        self,
        position: Position,
        label: CaseLabel,
        body_block: FunctionBodyBlock,
    ) -> None:
        self.label = label
        self.body = body_block
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> CaseBlock:
        assert len(children) == 3
        case_token, case_label, body_block = children
        assert isinstance(case_token, Token)
        assert isinstance(case_label, CaseLabel)
        assert isinstance(body_block, FunctionBodyBlock)

        return CaseBlock(case_token.position, case_label, body_block)


class DefaultBlock(AaaParseModel):
    def __init__(self, position: Position, body_block: FunctionBodyBlock) -> None:
        self.body_block = body_block
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> DefaultBlock:
        assert len(children) == 2
        default_token, body_block = children

        assert isinstance(default_token, Token)
        assert isinstance(body_block, FunctionBodyBlock)

        return DefaultBlock(default_token.position, body_block)


class MatchBlock(AaaParseModel):
    def __init__(
        self, position: Position, blocks: list[CaseBlock | DefaultBlock]
    ) -> None:
        self.blocks = blocks
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> MatchBlock:
        blocks: list[CaseBlock | DefaultBlock] = []
        match_token = children[0]
        assert isinstance(match_token, Token)

        for child in children[2:-1]:
            assert isinstance(child, CaseBlock | DefaultBlock)
            blocks.append(child)

        return MatchBlock(match_token.position, blocks)


class EnumVariant(AaaParseModel):
    def __init__(
        self,
        name: Identifier,
        associated_data: EnumVariantAssociatedData | None,
    ) -> None:
        self.name = name
        self.associated_data = associated_data
        super().__init__(name.position)

    def get_data(self) -> list[TypeLiteral | FunctionPointerTypeLiteral]:
        if self.associated_data is None:
            return []
        data = self.associated_data.value
        if isinstance(data, TypeOrFunctionPointerLiteral):
            return [data.literal]
        return [item.literal for item in data.value]

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> EnumVariant:
        name = children[0]
        assert isinstance(name, Identifier)

        if len(children) == 3:
            data = children[2]
            assert isinstance(data, EnumVariantAssociatedData)
        else:
            data = None

        return EnumVariant(name, data)


class EnumVariants(AaaParseModel):
    def __init__(self, variants: list[EnumVariant]) -> None:
        assert len(variants) >= 1

        self.value = variants
        super().__init__(variants[0].position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> EnumVariants:
        variants: list[EnumVariant] = []

        for child in children:
            if isinstance(child, EnumVariant):
                variants.append(child)
            elif isinstance(child, Token):
                pass  # ignore commas
            else:
                raise NotImplementedError

        return EnumVariants(variants)


class Enum(AaaParseModel):
    def __init__(self, declaration: EnumDeclaration, variants: EnumVariants) -> None:
        self.declaration = declaration
        self.variants = variants
        super().__init__(declaration.position)

    def get_variants(self) -> list[EnumVariant]:
        return self.variants.value

    def get_name(self) -> str:
        return self.declaration.name.value

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> Enum:
        assert len(children) == 4
        declaration, _, variants, _ = children

        assert isinstance(declaration, EnumDeclaration)
        assert isinstance(variants, EnumVariants)

        return Enum(declaration, variants)


class EnumVariantAssociatedData(AaaParseModel):
    def __init__(
        self,
        position: Position,
        data: TypeOrFunctionPointerLiteral | CommaSeparatedTypeList,
    ) -> None:
        self.value = data
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> EnumVariantAssociatedData:
        position = children[0].position

        data: TypeOrFunctionPointerLiteral | CommaSeparatedTypeList
        if isinstance(children[0], TypeOrFunctionPointerLiteral):
            data = children[0]
        else:
            assert isinstance(children[1], CommaSeparatedTypeList)
            data = children[1]

        return EnumVariantAssociatedData(position, data)


class Never(AaaParseModel):
    ...


class FunctionBodyItem(AaaParseModel):
    types = (
        Assignment
        | Boolean
        | Branch
        | Call
        | Char
        | ForeachLoop
        | FunctionCall
        | FunctionPointerTypeLiteral
        | GetFunctionPointer
        | Integer
        | MatchBlock
        | Return
        | String
        | StructFieldQuery
        | StructFieldUpdate
        | UseBlock
        | WhileLoop
    )

    def __init__(self, position: Position, value: types) -> None:
        self.value = value
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FunctionBodyItem:
        assert len(children) == 1
        child = children[0]

        assert isinstance(child, FunctionBodyItem.types.__args__)  # type:ignore
        return FunctionBodyItem(child.position, child)


class FunctionBodyBlock(AaaParseModel):
    def __init__(
        self,
        position: Position,
        body: FunctionBody,
        end_token_position: Position,
    ) -> None:
        self.value = body
        self.end_token_position = end_token_position
        super().__init__(position)

    @classmethod
    def load(cls, children: list[AaaParseModel | Token]) -> FunctionBodyBlock:
        assert len(children) == 3
        start_token, body, end_token = children
        assert isinstance(start_token, Token)
        assert isinstance(body, FunctionBody)
        assert isinstance(end_token, Token)

        return FunctionBodyBlock(start_token.position, body, end_token.position)


class ParserOutput(AaaModel):
    def __init__(
        self,
        parsed: dict[Path, SourceFile],
        entrypoint: Path,
        builtins_path: Path,
    ) -> None:
        self.parsed = parsed
        self.entrypoint = entrypoint
        self.builtins_path = builtins_path
