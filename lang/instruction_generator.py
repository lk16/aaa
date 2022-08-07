from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

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
    BooleanLiteral,
    Branch,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    MemberFunctionName,
    Operator,
    ParsedType,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
)
from lang.models.program import ProgramImport
from lang.models.typing import RootType, VariableType

if TYPE_CHECKING:  # pragma: nocover
    from lang.runtime.program import Program

OPERATOR_INSTRUCTIONS: Dict[str, Instruction] = {  # TODO move non-operators out
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
    "close": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_CLOSE),
    "environ": StandardLibraryCall(kind=StandardLibraryCallKind.ENVIRON),
    "exit": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_EXIT),
    "execve": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_EXECVE),
    "fork": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_FORK),
    "fsync": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_FSYNC),
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
    "str:append": StandardLibraryCall(kind=StandardLibraryCallKind.STR_APPEND),
    "str:contains": StandardLibraryCall(kind=StandardLibraryCallKind.STR_CONTAINS),
    "str:equals": StandardLibraryCall(kind=StandardLibraryCallKind.STR_EQUALS),
    "str:find": StandardLibraryCall(kind=StandardLibraryCallKind.STR_FIND),
    "str:find_after": StandardLibraryCall(kind=StandardLibraryCallKind.STR_FIND_AFTER),
    "str:join": StandardLibraryCall(kind=StandardLibraryCallKind.STR_JOIN),
    "str:len": StandardLibraryCall(kind=StandardLibraryCallKind.STR_LEN),
    "str:lower": StandardLibraryCall(kind=StandardLibraryCallKind.STR_LOWER),
    "str:replace": StandardLibraryCall(kind=StandardLibraryCallKind.STR_REPLACE),
    "str:strip": StandardLibraryCall(kind=StandardLibraryCallKind.STR_STRIP),
    "str:split": StandardLibraryCall(kind=StandardLibraryCallKind.STR_SPLIT),
    "str:substr": StandardLibraryCall(kind=StandardLibraryCallKind.STR_SUBSTR),
    "str:to_bool": StandardLibraryCall(kind=StandardLibraryCallKind.STR_TO_BOOL),
    "str:to_int": StandardLibraryCall(kind=StandardLibraryCallKind.STR_TO_INT),
    "str:upper": StandardLibraryCall(kind=StandardLibraryCallKind.STR_UPPER),
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
    "write": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_WRITE),
    "waitpid": StandardLibraryCall(kind=StandardLibraryCallKind.SYSCALL_WAITPID),
}


class InstructionGenerator:
    def __init__(self, file: Path, function: Function, program: "Program") -> None:
        self.function = function
        self.file = file
        self.program = program

    def generate_instructions(self) -> List[Instruction]:
        return self.instructions_for_function_body(self.function.body, 0)

    def instructions_for_integer_literal(
        self, integer_literal: IntegerLiteral
    ) -> List[Instruction]:
        return [PushInt(value=integer_literal.value)]

    def instructions_for_string_literal(
        self, string_literal: StringLiteral
    ) -> List[Instruction]:
        return [PushString(value=string_literal.value)]

    def instructions_for_boolean_literal(
        self, boolean_literal: BooleanLiteral
    ) -> List[Instruction]:
        return [PushBool(value=boolean_literal.value)]

    def instructions_for_operator(self, operator: Operator) -> List[Instruction]:
        return [OPERATOR_INSTRUCTIONS[operator.value]]

    def instructions_for_loop(self, loop: Loop, offset: int) -> List[Instruction]:
        condition_instructions = self.instructions_for_function_body(
            loop.condition, offset
        )
        body_offset = offset + 1 + len(condition_instructions) + 1

        body_instructions = self.instructions_for_function_body(loop.body, body_offset)
        beyond_loop_nop_offset = body_offset + len(body_instructions) + 1

        loop_instructions: List[Instruction] = []

        loop_instructions += [Nop()]
        loop_instructions += condition_instructions
        loop_instructions += [JumpIfNot(instruction_offset=beyond_loop_nop_offset)]
        loop_instructions += body_instructions
        loop_instructions += [Jump(instruction_offset=offset)]
        loop_instructions += [Nop()]

        return loop_instructions

    def instructions_for_identfier(self, identifier: Identifier) -> List[Instruction]:
        # TODO refactor

        for argument in self.function.arguments:
            if identifier.name == argument.name:
                return [PushFunctionArgument(arg_name=argument.name)]

        if identifier.name in OPERATOR_INSTRUCTIONS:
            return [OPERATOR_INSTRUCTIONS[identifier.name]]

        identified = self.program.get_identifier(self.file, identifier.name)
        assert identified

        if isinstance(identified, ProgramImport):
            # If this is an import, copy from other file
            identified = self.program.get_identifier(
                identified.source_file, identified.original_name
            )

        if isinstance(identified, Function):
            source_file, original_name = self.program.get_function_source_and_name(
                self.file, identifier.name
            )
            return [CallFunction(func_name=original_name, file=source_file)]
        elif isinstance(identified, Struct):
            return [PushStruct(type=identified)]
        else:  # pragma: nocover
            assert False

    def instructions_for_branch(self, branch: Branch, offset: int) -> List[Instruction]:
        branch_instructions: List[Instruction] = []

        condition_instructions = self.instructions_for_function_body(
            branch.condition, offset
        )

        if_offset = offset + 1 + len(condition_instructions)
        if_instructions = self.instructions_for_function_body(branch.if_body, if_offset)

        else_nop_offset = if_offset + len(if_instructions) + 1
        else_offset = else_nop_offset + 1
        else_instructions = self.instructions_for_function_body(
            branch.else_body, else_offset
        )

        branch_end_nop_offset = else_offset + len(else_instructions)

        branch_instructions = condition_instructions
        branch_instructions += [JumpIfNot(instruction_offset=else_nop_offset)]
        branch_instructions += if_instructions
        branch_instructions += [Jump(instruction_offset=branch_end_nop_offset)]
        branch_instructions += [Nop()]
        branch_instructions += else_instructions
        branch_instructions += [Nop()]
        return branch_instructions

    def instructions_for_function_body(
        self, function_body: FunctionBody, offset: int
    ) -> List[Instruction]:
        instructions: List[Instruction] = []

        for child in function_body.items:
            child_offset = offset + len(instructions)

            if isinstance(child, BooleanLiteral):
                instructions += self.instructions_for_boolean_literal(child)
            elif isinstance(child, Branch):
                instructions += self.instructions_for_branch(child, child_offset)
            elif isinstance(child, FunctionBody):
                instructions += self.instructions_for_function_body(child, child_offset)
            elif isinstance(child, Identifier):
                instructions += self.instructions_for_identfier(child)
            elif isinstance(child, IntegerLiteral):
                instructions += self.instructions_for_integer_literal(child)
            elif isinstance(child, Loop):
                instructions += self.instructions_for_loop(child, child_offset)
            elif isinstance(child, MemberFunctionName):
                instructions += self.instructions_for_member_function(
                    child, child_offset
                )
            elif isinstance(child, Operator):
                instructions += self.instructions_for_operator(child)
            elif isinstance(child, ParsedType):
                instructions += self.instructions_for_parsed_type(child)
            elif isinstance(child, StringLiteral):
                instructions += self.instructions_for_string_literal(child)
            elif isinstance(child, StructFieldQuery):
                instructions += self.instructions_for_struct_field_query(child)
            elif isinstance(child, StructFieldUpdate):
                instructions += self.instructions_for_struct_field_update(
                    child, child_offset
                )
            else:  # pragma: nocover
                assert False

        return instructions

    def instructions_for_parsed_type(
        self, parsed_type: ParsedType
    ) -> List[Instruction]:
        # TODO make type-independent Push() instruction
        # and use it with Variable.zero_value() instead

        var_type = VariableType.from_parsed_type(parsed_type)

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
        self, member_function_name: MemberFunctionName, offset: int
    ) -> List[Instruction]:
        # TODO we should need this list hardcoded here
        if member_function_name.type_name in ["bool", "int", "str", "vec", "map"]:
            key = f"{member_function_name.type_name}:{member_function_name.func_name}"
            return [OPERATOR_INSTRUCTIONS[key]]

        key = f"{member_function_name.type_name}:{member_function_name.func_name}"
        identified = self.program.identifiers[self.file][key]

        assert isinstance(identified, Function)
        source_file, original_name = self.program.get_function_source_and_name(
            self.file, key
        )
        return [CallFunction(func_name=original_name, file=source_file)]

    def instructions_for_struct_field_query(
        self, field_query: StructFieldQuery
    ) -> List[Instruction]:
        return [PushString(value=field_query.field_name.value), GetStructField()]

    def instructions_for_struct_field_update(
        self, field_update: StructFieldUpdate, offset: int
    ) -> List[Instruction]:
        instructions: List[Instruction] = []
        instructions += [PushString(value=field_update.field_name.value)]
        instructions += self.instructions_for_function_body(
            field_update.new_value_expr, offset + 1
        )
        instructions += [SetStructField()]
        return instructions
