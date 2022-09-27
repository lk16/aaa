from pathlib import Path
from typing import Dict, List, Tuple

from aaa.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    Identifier,
    IdentifierCallingFunction,
    IdentifierCallingType,
    IdentifierUsingArgument,
    IntegerLiteral,
    Loop,
    MemberFunctionName,
    Operator,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Unresolved,
)
from aaa.instruction_generator.models import (
    And,
    Assert,
    CallFunction,
    Divide,
    Drop,
    Dup,
    Equals,
    GetStructField,
    Instruction,
    InstructionGeneratorOutput,
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
    PushString,
    Rot,
    SetStructField,
    StandardLibraryCall,
    StandardLibraryCallKind,
    Swap,
)

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
}

STDLIB_INSTRUCTIONS: Dict[str, StandardLibraryCallKind] = {
    "chdir": StandardLibraryCallKind.SYSCALL_CHDIR,
    "close": StandardLibraryCallKind.SYSCALL_CLOSE,
    "environ": StandardLibraryCallKind.ENVIRON,
    "execve": StandardLibraryCallKind.SYSCALL_EXECVE,
    "exit": StandardLibraryCallKind.SYSCALL_EXIT,
    "fork": StandardLibraryCallKind.SYSCALL_FORK,
    "fsync": StandardLibraryCallKind.SYSCALL_FSYNC,
    "getcwd": StandardLibraryCallKind.SYSCALL_GETCWD,
    "getenv": StandardLibraryCallKind.GETENV,
    "getpid": StandardLibraryCallKind.SYSCALL_GETPID,
    "getppid": StandardLibraryCallKind.SYSCALL_GETPPID,
    "map:clear": StandardLibraryCallKind.MAP_CLEAR,
    "map:copy": StandardLibraryCallKind.MAP_COPY,
    "map:drop": StandardLibraryCallKind.MAP_DROP,
    "map:empty": StandardLibraryCallKind.MAP_EMPTY,
    "map:get": StandardLibraryCallKind.MAP_GET,
    "map:has_key": StandardLibraryCallKind.MAP_HAS_KEY,
    "map:keys": StandardLibraryCallKind.MAP_KEYS,
    "map:pop": StandardLibraryCallKind.MAP_POP,
    "map:set": StandardLibraryCallKind.MAP_SET,
    "map:size": StandardLibraryCallKind.MAP_SIZE,
    "map:values": StandardLibraryCallKind.MAP_VALUES,
    "open": StandardLibraryCallKind.SYSCALL_OPEN,
    "read": StandardLibraryCallKind.SYSCALL_READ,
    "setenv": StandardLibraryCallKind.SETENV,
    "str:append": StandardLibraryCallKind.STR_APPEND,
    "str:contains": StandardLibraryCallKind.STR_CONTAINS,
    "str:equals": StandardLibraryCallKind.STR_EQUALS,
    "str:find_after": StandardLibraryCallKind.STR_FIND_AFTER,
    "str:find": StandardLibraryCallKind.STR_FIND,
    "str:join": StandardLibraryCallKind.STR_JOIN,
    "str:len": StandardLibraryCallKind.STR_LEN,
    "str:lower": StandardLibraryCallKind.STR_LOWER,
    "str:replace": StandardLibraryCallKind.STR_REPLACE,
    "str:split": StandardLibraryCallKind.STR_SPLIT,
    "str:strip": StandardLibraryCallKind.STR_STRIP,
    "str:substr": StandardLibraryCallKind.STR_SUBSTR,
    "str:to_bool": StandardLibraryCallKind.STR_TO_BOOL,
    "str:to_int": StandardLibraryCallKind.STR_TO_INT,
    "str:upper": StandardLibraryCallKind.STR_UPPER,
    "time": StandardLibraryCallKind.SYSCALL_TIME,
    "unsetenv": StandardLibraryCallKind.UNSETENV,
    "vec:clear": StandardLibraryCallKind.VEC_CLEAR,
    "vec:copy": StandardLibraryCallKind.VEC_COPY,
    "vec:empty": StandardLibraryCallKind.VEC_EMPTY,
    "vec:get": StandardLibraryCallKind.VEC_GET,
    "vec:pop": StandardLibraryCallKind.VEC_POP,
    "vec:push": StandardLibraryCallKind.VEC_PUSH,
    "vec:set": StandardLibraryCallKind.VEC_SET,
    "vec:size": StandardLibraryCallKind.VEC_SIZE,
    "waitpid": StandardLibraryCallKind.SYSCALL_WAITPID,
    "write": StandardLibraryCallKind.SYSCALL_WRITE,
}


class InstructionGenerator:
    def __init__(self, cross_reference_output: CrossReferencerOutput) -> None:
        self.identifiers = cross_reference_output.identifiers
        self.builtins_path = cross_reference_output.builtins_path
        self.instructions_dict: Dict[Tuple[Path, str], List[Instruction]] = {}

    def run(self) -> InstructionGeneratorOutput:
        for function in self.identifiers.values():
            if isinstance(function, Function):
                self.instructions_dict[
                    function.identify()
                ] = self.generate_instructions(function)

        return InstructionGeneratorOutput(instructions=self.instructions_dict)

    def generate_instructions(self, function: Function) -> List[Instruction]:
        assert not isinstance(function.body, Unresolved)
        return self.instructions_for_function_body(function.body, 0)

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

        assert not isinstance(identifier.kind, Unresolved)

        if isinstance(identifier.kind, IdentifierCallingFunction):
            called_function = identifier.kind.function

            if called_function.file == self.builtins_path:
                return [
                    StandardLibraryCall(kind=STDLIB_INSTRUCTIONS[called_function.name])
                ]

            return [
                CallFunction(
                    func_name=called_function.func_name, file=called_function.file
                )
            ]

        if isinstance(identifier.kind, IdentifierCallingType):
            # TODO need Variable type for identifier.kind.type
            # TODO handle builtin types nicely / update PushStruct instruction
            raise NotImplementedError

        if isinstance(identifier.kind, IdentifierUsingArgument):
            # TODO use argument type
            return [PushFunctionArgument(arg_name=identifier.name)]

        assert False  # pragma: nocover

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

    def instructions_for_member_function(
        self, member_function_name: MemberFunctionName, offset: int
    ) -> List[Instruction]:
        # TODO consider handling as Identifier
        raise NotImplementedError

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
