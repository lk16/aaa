from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Type

from lang.instructions.types import (
    And,
    Assert,
    BoolPush,
    CallFunction,
    CharNewLinePrint,
    Divide,
    Drop,
    Dup,
    Equals,
    Instruction,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPush,
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
    PushFunctionArgument,
    Rot,
    StringLength,
    StringPush,
    SubString,
    Swap,
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
    Operator,
    StringLiteral,
)

if TYPE_CHECKING:  # pragma: nocover
    from lang.runtime.program import Program

OPERATOR_INSTRUCTIONS: Dict[str, Instruction] = {
    "-": Minus(),
    "!=": IntNotEqual(),
    ".": Print(),
    "*": Multiply(),
    "/": Divide(),
    "\\n": CharNewLinePrint(),
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
}


class InstructionGenerator:
    def __init__(self, file: Path, function: Function, program: "Program") -> None:
        self.function = function
        self.file = file
        self.program = program

        self.instruction_funcs: Dict[
            Type[AaaTreeNode], Callable[[AaaTreeNode, int], List[Instruction]]
        ] = {
            IntegerLiteral: self.instructions_for_integer_literal,
            StringLiteral: self.instructions_for_string_literal,
            BooleanLiteral: self.instructions_for_boolean_literal,
            Operator: self.instructions_for_operator,
            Loop: self.instructions_for_loop,
            Identifier: self.instructions_for_identfier,
            Branch: self.instructions_for_branch,
            FunctionBody: self.instructions_for_function_body,
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
        return [IntPush(node.value)]

    def instructions_for_string_literal(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, StringLiteral)
        return [StringPush(node.value)]

    def instructions_for_boolean_literal(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, BooleanLiteral)
        return [BoolPush(node.value)]

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

        if identifier in {arg.name for arg in self.function.arguments}:
            return [PushFunctionArgument(identifier)]

        source_file, original_name = self.program.get_function_source_and_name(
            self.file, identifier
        )
        return [CallFunction(func_name=original_name, file=source_file)]

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
