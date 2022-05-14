from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Type

from lang.instructions.types import (
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
    MapClear,
    MapCopy,
    MapDrop,
    MapEmpty,
    MapGet,
    MapHasKey,
    MapKeys,
    MapPop,
    MapSet,
    MapSize,
    MapValues,
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
    StringLength,
    SubString,
    Swap,
    VecClear,
    VecCopy,
    VecEmpty,
    VecGet,
    VecPop,
    VecPush,
    VecSet,
    VecSize,
)
from lang.runtime.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    MemberFunction,
    Operator,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
)
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
    "strlen": StringLength(),
    "substr": SubString(),
    "swap": Swap(),
    "vec:clear": VecClear(),
    "vec:copy": VecCopy(),
    "vec:empty": VecEmpty(),
    "vec:get": VecGet(),
    "vec:pop": VecPop(),
    "vec:push": VecPush(),
    "vec:set": VecSet(),
    "vec:size": VecSize(),
    "map:get": MapGet(),
    "map:set": MapSet(),
    "map:has_key": MapHasKey(),
    "map:size": MapSize(),
    "map:empty": MapEmpty(),
    "map:pop": MapPop(),
    "map:drop": MapDrop(),
    "map:clear": MapClear(),
    "map:copy": MapCopy(),
    "map:keys": MapKeys(),
    "map:values": MapValues(),
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
            MemberFunction: self.instructions_for_member_function,
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
        return [PushInt(node.value)]

    def instructions_for_string_literal(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, StringLiteral)
        return [PushString(node.value)]

    def instructions_for_boolean_literal(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, BooleanLiteral)
        return [PushBool(node.value)]

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
        loop_instructions += [JumpIfNot(beyond_loop_end)]
        loop_instructions += body_instructions
        loop_instructions += [Jump(offset)]

        return loop_instructions

    def instructions_for_identfier(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Identifier)

        identifier = node.name

        for argument in self.function.arguments:
            if node.name == argument.name:
                return [PushFunctionArgument(argument.name)]

        identified = self.program.identifiers[self.file][identifier]

        if isinstance(identified, Function):
            source_file, original_name = self.program.get_function_source_and_name(
                self.file, identifier
            )
            return [CallFunction(func_name=original_name, file=source_file)]
        elif isinstance(identified, Struct):
            return [PushStruct(identified)]
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
        branch_instructions += [JumpIfNot(else_offset)]
        branch_instructions += if_instructions
        branch_instructions += [Jump(beyond_else_offset)]
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
            return [PushInt(0)]

        elif root_type == RootType.BOOL:
            return [PushBool(False)]

        elif root_type == RootType.STRING:
            return [PushString("")]

        elif root_type == RootType.VECTOR:
            return [PushVec(var_type.get_variable_type_param(0))]

        elif root_type == RootType.MAPPING:
            return [
                PushMap(
                    var_type.get_variable_type_param(0),
                    var_type.get_variable_type_param(1),
                )
            ]

        else:  # pragma: nocover
            assert False

    def instructions_for_member_function(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, MemberFunction)

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
        return [PushString(node.field_name.value), GetStructField()]

    def instructions_for_struct_field_update(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, StructFieldUpdate)
        instructions: List[Instruction] = []
        instructions += [PushString(node.field_name.value)]
        instructions += self.instructions_for_function_body(
            node.new_value_expr, offset + 1
        )
        instructions += [SetStructField()]
        return instructions
