from typing import Callable, Dict, List, Type

from lang.instruction_types import (
    And,
    BoolPush,
    CallFunction,
    CharNewLinePrint,
    Divide,
    Drop,
    Dup,
    Else,
    End,
    Equals,
    If,
    Instruction,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPush,
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
    While,
    WhileEnd,
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

    def generate_instructions(self) -> List[Instruction]:
        return self._generate_instructions(self.function.body, 0)

    def _generate_instructions(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:

        funcs: Dict[
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

        return funcs[type(node)](node, offset)

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

        # TODO do something smarter when loop_body is empty

        body_instructions = self._generate_instructions(node.body, offset + 1)

        end_offset = offset + 1 + len(body_instructions)

        loop_instructions: List[Instruction] = []

        loop_instructions += [While(end_offset)]
        loop_instructions += body_instructions
        loop_instructions += [WhileEnd(offset)]

        return loop_instructions

    def instructions_for_identfier(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Identifier)

        identifier = node.name

        if identifier in self.function.arguments:
            return [PushFunctionArgument(identifier)]

        # TODO confirm that function by this name actually exists
        # so we don't crash at runtime
        return [CallFunction(identifier)]

    def instructions_for_branch(
        self, node: AaaTreeNode, offset: int
    ) -> List[Instruction]:
        assert isinstance(node, Branch)

        # TODO do something smarter when if_body or else_body are empty

        if_instructions = self._generate_instructions(node.if_body, offset + 1)

        else_offset = offset + 1 + len(if_instructions)
        else_instructions = self._generate_instructions(node.else_body, else_offset + 1)
        end_offset = else_offset + 1 + len(else_instructions)

        branch_instructions: List[Instruction] = []

        branch_instructions += [If(else_offset)]
        branch_instructions += if_instructions
        branch_instructions += [Else(end_offset)]
        branch_instructions += else_instructions
        branch_instructions += [End()]

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
