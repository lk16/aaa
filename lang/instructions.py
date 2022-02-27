from typing import Dict, List

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
    File,
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
    "equals": Equals(),
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
    return _get_instructions(function, function.arguments, 0)


def _get_instructions(  # TODO refactor into small handler functions
    node: AaaTreeNode, func_args: List[str], offset: int
) -> List[Instruction]:
    if isinstance(node, IntegerLiteral):
        return [IntPush(node.value)]

    elif isinstance(node, StringLiteral):
        return [StringPush(node.value)]

    elif isinstance(node, BooleanLiteral):
        return [BoolPush(node.value)]

    elif isinstance(node, Operator):
        if node.value not in OPERATOR_INSTRUCTIONS:
            # TODO unhandled operator
            raise NotImplementedError

        return [OPERATOR_INSTRUCTIONS[node.value]]

    elif isinstance(node, Loop):
        # TODO do something smarter when loop_body is empty

        body_instructions = _get_instructions(node.body, func_args, offset + 1)

        loop_instructions: List[Instruction] = []

        loop_instructions += [While(offset + len(body_instructions))]
        loop_instructions += body_instructions
        loop_instructions += [WhileEnd(offset)]

        return loop_instructions

    elif isinstance(node, Identifier):
        identifier = node.name

        if identifier in func_args:
            return [PushFunctionArgument(identifier)]

        # TODO confirm that function by this name actually exists
        # so we don't crash at runtime
        return [CallFunction(identifier)]

    elif isinstance(node, Branch):
        # TODO do something smarter when if_body or else_body are empty

        if_instructions = _get_instructions(node.if_body, func_args, offset + 1)

        else_offset = offset + 1 + len(if_instructions)
        else_instructions = _get_instructions(
            node.else_body, func_args, else_offset + 1
        )
        end_offset = else_offset + 1 + len(else_instructions)

        branch_instructions: List[Instruction] = []

        branch_instructions += [If(else_offset)]
        branch_instructions += if_instructions
        branch_instructions += [Else(end_offset)]
        branch_instructions += else_instructions
        branch_instructions += [End()]

        return branch_instructions

    elif isinstance(node, FunctionBody):
        instructions: List[Instruction] = []

        for child in node.items:
            child_offset = offset + len(instructions)
            instructions = _get_instructions(child, func_args, child_offset)

        return instructions

    elif isinstance(node, Function):
        return _get_instructions(node.body, func_args, offset)

    elif isinstance(node, File):  # pragma: nocover
        # A file has no instructions.
        raise NotImplementedError

    else:  # pragma: nocover
        # Unhandled AaaTreeNode subclass
        raise NotImplementedError
