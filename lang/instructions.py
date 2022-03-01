from typing import Callable, Dict, List, Type

from lang.instruction_types import (
    And,
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
    JumpIf,
    JumpIfNot,
    Minus,
    Modulo,
    Multiply,
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
from lang.parse import (
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

OPERATOR_INSTRUCTIONS: Dict[str, Instruction] = {
    "+": Plus(),
    "-": Minus(),
    "*": Multiply(),
    "/": Divide(),
    "%": Modulo(),
    "and": And(),
    "or": Or(),
    "not": Not(),
    "=": Equals(),
    ">": IntGreaterThan(),
    ">=": IntGreaterEquals(),
    "<": IntLessThan(),
    "<=": IntLessEquals(),
    "!=": IntNotEqual(),
    "drop": Drop(),
    "dup": Dup(),
    "swap": Swap(),
    "over": Over(),
    "rot": Rot(),
    "\\n": CharNewLinePrint(),
    ".": Print(),
    "substr": SubString(),
    "strlen": StringLength(),
}


def get_instructions(function: Function) -> List[Instruction]:
    if function._instructions is None:
        function._instructions = InstructionGenerator(function).generate_instructions()

    return function._instructions


class InstructionGenerator:
    def __init__(self, function: Function) -> None:
        self.function = function

        self.instruction_funcs: Dict[
            Type[AaaTreeNode], Callable[[AaaTreeNode, int], List[Instruction]]
        ] = {
            IntegerLiteral: self.integer_liter_instructions,
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

    def integer_liter_instructions(
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

        if node.value not in OPERATOR_INSTRUCTIONS:
            # TODO unhandled operator
            raise NotImplementedError

        return [OPERATOR_INSTRUCTIONS[node.value]]

    def instructions_for_loop(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Loop)

        body_instructions = self._generate_instructions(node.body, offset + 1)

        beyond_loop_end = offset + 2 + len(body_instructions)

        loop_instructions: List[Instruction] = []

        loop_instructions += [JumpIfNot(beyond_loop_end)]
        loop_instructions += body_instructions
        loop_instructions += [JumpIf(offset + 1)]

        return loop_instructions

    def instructions_for_identfier(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Identifier)

        identifier = node.name

        if identifier in self.function.arguments:
            return [PushFunctionArgument(identifier)]

        # If it's not an arugment, we must be calling a function.
        # Whether a function by that name exists will be checked in Program.
        return [CallFunction(identifier)]

    def instructions_for_branch(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Branch)

        branch_instructions: List[Instruction] = []

        if len(node.if_body.items) != 0:
            if len(node.else_body.items) == 0:
                # Non-empty if, empty else: we only need one jump
                if_instructions = self._generate_instructions(node.if_body, offset + 1)
                if_fail_jump = offset + 1 + len(if_instructions)

                branch_instructions = [JumpIfNot(if_fail_jump)]
                branch_instructions += if_instructions
                return branch_instructions

            else:
                if_instructions = self._generate_instructions(node.if_body, offset + 1)
                if_fail_jump = offset + 2 + len(if_instructions)
                else_instructions = self._generate_instructions(
                    node.else_body, offset + len(if_instructions) + 2
                )
                if_end_jump = if_fail_jump + len(else_instructions)

                branch_instructions = [JumpIfNot(if_fail_jump)]
                branch_instructions += if_instructions
                branch_instructions += [Jump(if_end_jump)]
                branch_instructions += else_instructions
                return branch_instructions

        else:
            if len(node.else_body.items) == 0:
                # Empty if-else: consume Jump boolean
                return [Drop()]

            else:
                # Empty if, non-empty else: we only need one jump
                else_instructions = self._generate_instructions(
                    node.else_body, offset + 1
                )
                else_fail_jump = offset + 1 + len(else_instructions)

                branch_instructions = [JumpIf(else_fail_jump)]
                branch_instructions += else_instructions
                return branch_instructions

        # Unreachable
        raise NotImplementedError

    def instructions_for_function_body(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, FunctionBody)

        instructions: List[Instruction] = []

        for child in node.items:
            child_offset = offset + len(instructions)
            instructions += self._generate_instructions(child, child_offset)

        return instructions
