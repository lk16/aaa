from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Type

from lang.models.instructions import (
    And,
    Assert,
    CallFunction,
    Divide,
    Drop,
    Dup,
    Equals,
    GetStructField,
    Instruction,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    Jump,
    JumpIfNot,
    Minus,
    Modulo,
    Multiply,
    Nop,
    Not,
    Or,
    Over,
    Plus,
    Print,
    PushBool,
    PushFunctionArgument,
    PushInt,
    PushMap,
    PushString,
    PushStruct,
    PushVec,
    Rot,
    SetStructField,
    StandardLibraryCall,
    StandardLibraryCallKind,
    Swap,
)
from lang.models.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    MemberFunctionName,
    Operator,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
)
from lang.models.program import ProgramImport
from lang.typing.types import RootType, VariableType

if TYPE_CHECKING:  # pragma: nocover
    from lang.runtime.program import Program

OPERATOR_INSTRUCTIONS: Dict[str, Instruction] = {
    "-": Minus(),
    "!=": IntNotEqual(),
    ".": Print(),
    "*": Multiply(),
    "/": Divide(),
    "%": Modulo(),
    "+": Plus(),
    "<": IntLessThan(),
    "<=": IntLessEquals(),
    "=": Equals(),
    ">": IntGreaterThan(),
    ">=": IntGreaterEquals(),
    "and": And(),
    "assert": Assert(),
    "drop": Drop(),
    "dup": Dup(),
    "nop": Nop(),
    "not": Not(),
    "or": Or(),
    "over": Over(),
    "rot": Rot(),
    "swap": Swap(),
    "chdir": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_CHDIR),
    "environ": StandardLibraryCall(kind=StandardLibraryCallKind.ENVIRON),
    "exit": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_EXIT),
    "getcwd": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_GETCWD),
    "getenv": StandardLibraryCall(kind=StandardLibraryCallKind.GETENV),
    "getpid": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_GETPID),
    "getppid": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_GETPPID),
    "map:clear": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_CLEAR),
    "map:copy": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_COPY),
    "map:drop": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_DROP),
    "map:empty": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_EMPTY),
    "map:get": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_GET),
    "map:has_key": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_HAS_KEY),
    "map:keys": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_KEYS),
    "map:pop": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_POP),
    "map:set": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_SET),
    "map:size": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_SIZE),
    "map:values": StandardLibraryCall(kind=StandardLibraryCallKind.MAP_VALUES),
    "open": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_OPEN),
    "read": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_READ),
    "setenv": StandardLibraryCall(kind=StandardLibraryCallKind.SETENV),
    "time": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_TIME),
    "unsetenv": StandardLibraryCall(kind=StandardLibraryCallKind.UNSETENV),
    "vec:clear": StandardLibraryCall(kind=StandardLibraryCallKind.VEC_CLEAR),
    "vec:copy": StandardLibraryCall(kind=StandardLibraryCallKind.VEC_COPY),
    "vec:empty": StandardLibraryCall(kind=StandardLibraryCallKind.VEC_EMPTY),
    "vec:get": StandardLibraryCall(kind=StandardLibraryCallKind.VEC_GET),
    "vec:pop": StandardLibraryCall(kind=StandardLibraryCallKind.VEC_POP),
    "vec:push": StandardLibraryCall(kind=StandardLibraryCallKind.VEC_PUSH),
    "vec:set": StandardLibraryCall(kind=StandardLibraryCallKind.VEC_SET),
    "vec:size": StandardLibraryCall(kind=StandardLibraryCallKind.VEC_SIZE),
}


class InstructionGenerator:
    def __init__(self, file: Path, function: Function, program: "Program") -> None:
        self.function = function
        self.file = file
        self.program = program

        self.instruction_funcs: Dict[
            Type[AaaTreeNode], Callable[[AaaTreeNode, int], List[Instruction]]
        ] = {
            BooleanLiteral: self.instructions_for_boolean_literal,
            Branch: self.instructions_for_branch,
            FunctionBody: self.instructions_for_function_body,
            Identifier: self.instructions_for_identfier,
            IntegerLiteral: self.instructions_for_integer_literal,
            Loop: self.instructions_for_loop,
            MemberFunctionName: self.instructions_for_member_function,
            Operator: self.instructions_for_operator,
            StringLiteral: self.instructions_for_string_literal,
            StructFieldQuery: self.instructions_for_struct_field_query,
            StructFieldUpdate: self.instructions_for_struct_field_update,
            TypeLiteral: self.instructions_for_type_literal,
        }

    def generate_instructions(self) -> List[Instruction]:
        return self._generate_instructions(self.function.body, 0)

    def _generate_instructions(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        return self.instruction_funcs[type(node)](node, offset)

    def instructions_for_integer_literal(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, IntegerLiteral)
        return [PushInt(value=node.value)]

    def instructions_for_string_literal(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, StringLiteral)
        return [PushString(value=node.value)]

    def instructions_for_boolean_literal(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, BooleanLiteral)
        return [PushBool(value=node.value)]

    def instructions_for_operator(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Operator)
        return [OPERATOR_INSTRUCTIONS[node.value]]

    def instructions_for_loop(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Loop)
        condition_instructions = self._generate_instructions(node.condition, offset)
        body_offset = offset + len(condition_instructions) + 2
        body_instructions = self._generate_instructions(node.body, body_offset)
        beyond_loop_end = body_offset + len(body_instructions)

        loop_instructions: List[Instruction] = []

        loop_instructions += condition_instructions
        loop_instructions += [JumpIfNot(instruction_offset=beyond_loop_end)]
        loop_instructions += body_instructions
        loop_instructions += [Jump(instruction_offset=offset)]

        return loop_instructions

    def instructions_for_identfier(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Identifier)

        identifier = node.name

        for argument in self.function.arguments:
            if node.name == argument.name:
                return [PushFunctionArgument(arg_name=argument.name)]

        if node.name in OPERATOR_INSTRUCTIONS:
            return [OPERATOR_INSTRUCTIONS[node.name]]

        identified = self.program.identifiers[self.file][identifier]

        if isinstance(identified, ProgramImport):
            # If this is an import, copy from other file
            identified = self.program.identifiers[identified.source_file][
                identified.original_name
            ]

        if isinstance(identified, Function):
            source_file, original_name = self.program.get_function_source_and_name(
                self.file, identifier
            )
            return [CallFunction(func_name=original_name, file=source_file)]
        elif isinstance(identified, Struct):
            return [PushStruct(type=identified)]
        else:  # pragma: nocover
            assert False

    def instructions_for_branch(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Branch)

        branch_instructions: List[Instruction] = []

        condition_instructions = self._generate_instructions(node.condition, offset)
        if_offset = offset + len(condition_instructions) + 1
        if_instructions = self._generate_instructions(node.if_body, if_offset)
        else_offset = if_offset + len(if_instructions) + 1
        else_instructions = self._generate_instructions(node.else_body, else_offset)
        beyond_else_offset = else_offset + len(else_instructions)

        branch_instructions = condition_instructions
        branch_instructions += [JumpIfNot(instruction_offset=else_offset)]
        branch_instructions += if_instructions
        branch_instructions += [Jump(instruction_offset=beyond_else_offset)]
        branch_instructions += else_instructions
        return branch_instructions

    def instructions_for_function_body(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, FunctionBody)

        instructions: List[Instruction] = []

        for child in node.items:
            child_offset = offset + len(instructions)
            instructions += self._generate_instructions(child, child_offset)

        return instructions

    def instructions_for_type_literal(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        # TODO make type-independent Push() instruction
        # and use it with Variable.zero_value() instead

        assert isinstance(node, TypeLiteral)
        var_type = VariableType.from_type_literal(node)

        root_type = var_type.root_type

        if root_type == RootType.INTEGER:
            return [PushInt(value=0)]

        elif root_type == RootType.BOOL:
            return [PushBool(value=False)]

        elif root_type == RootType.STRING:
            return [PushString(value="")]

        elif root_type == RootType.VECTOR:
            return [PushVec(item_type=var_type.get_variable_type_param(0))]

        elif root_type == RootType.MAPPING:
            return [
                PushMap(
                    key_type=var_type.get_variable_type_param(0),
                    value_type=var_type.get_variable_type_param(1),
                )
            ]

        else:  # pragma: nocover
            assert False

    def instructions_for_member_function(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, MemberFunctionName)

        if node.type_name in ["vec", "map"]:
            key = f"{node.type_name}:{node.func_name}"
            return [OPERATOR_INSTRUCTIONS[key]]

        member_function_name = f"{node.type_name}:{node.func_name}"
        identified = self.program.identifiers[self.file][member_function_name]

        assert isinstance(identified, Function)
        source_file, original_name = self.program.get_function_source_and_name(
            self.file, member_function_name
        )
        return [CallFunction(func_name=original_name, file=source_file)]

    def instructions_for_struct_field_query(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, StructFieldQuery)
        return [PushString(value=node.field_name.value), GetStructField()]

    def instructions_for_struct_field_update(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, StructFieldUpdate)
        instructions: List[Instruction] = []
        instructions += [PushString(value=node.field_name.value)]
        instructions += self.instructions_for_function_body(
            node.new_value_expr, offset + 1
        )
        instructions += [SetStructField()]
        return instructions
