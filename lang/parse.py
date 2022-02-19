from typing import Dict, List

from lang.exceptions import (
    BlockStackNotEmpty,
    InvalidBlockStackValue,
    UnexpectedOperation,
    UnhandledTokenType,
)
from lang.operations import (
    And,
    BoolPush,
    CharNewLinePrint,
    Divide,
    Drop,
    Dup,
    Else,
    End,
    If,
    IntEquals,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPush,
    Minus,
    Multiply,
    Not,
    Operation,
    Or,
    Over,
    Plus,
    Print,
    Rot,
    Swap,
    While,
    WhileEnd,
)
from lang.tokenize import Token, TokenType


def parse(tokens: List[Token]) -> List[Operation]:
    operations: List[Operation] = []

    # Stack of indexes in block start operations (such as If) in the operations list
    block_operations_offset_stack: List[int] = []

    for token in tokens:
        operation: Operation

        simple_tokens: Dict[TokenType, Operation] = {
            TokenType.PLUS: Plus(),
            TokenType.MINUS: Minus(),
            TokenType.STAR: Multiply(),
            TokenType.SLASH: Divide(),
            TokenType.TRUE: BoolPush(True),
            TokenType.FALSE: BoolPush(False),
            TokenType.AND: And(),
            TokenType.OR: Or(),
            TokenType.NOT: Not(),
            TokenType.EQUAL: IntEquals(),
            TokenType.GREATER_THAN: IntGreaterThan(),
            TokenType.GREATER_EQUAL: IntGreaterEquals(),
            TokenType.LESS_THAN: IntLessThan(),
            TokenType.LESS_EQUAL: IntLessEquals(),
            TokenType.NOT_EQUAL: IntNotEqual(),
            TokenType.DROP: Drop(),
            TokenType.DUPLICATE: Dup(),
            TokenType.SWAP: Swap(),
            TokenType.OVER: Over(),
            TokenType.ROTATE: Rot(),
            TokenType.PRINT_NEWLINE: CharNewLinePrint(),
            TokenType.PRINT: Print(),
        }

        if token.type in simple_tokens:
            operation = simple_tokens[token.type]

        elif token.type == TokenType.IF:
            operation = If(None)
            block_operations_offset_stack.append(len(operations))

        elif token.type == TokenType.ELSE:
            operation = Else(None)

            try:
                block_start_offset = block_operations_offset_stack.pop()
            except IndexError as e:
                # end without matching start block
                raise UnexpectedOperation(operation) from e

            block_start = operations[block_start_offset]

            if isinstance(block_start, If):
                block_start.jump_if_false = len(operations)

            else:  # pragma: nocover
                raise InvalidBlockStackValue(block_start)

            block_operations_offset_stack.append(len(operations))

        elif token.type == TokenType.END:
            operation = End()

            try:
                block_start_offset = block_operations_offset_stack.pop()
            except IndexError as e:
                # end without matching start block
                raise UnexpectedOperation(operation) from e

            block_start = operations[block_start_offset]

            if isinstance(block_start, If):
                block_start.jump_if_false = len(operations)

            elif isinstance(block_start, Else):
                block_start.jump_end = len(operations)
                pass

            elif isinstance(block_start, While):
                operation = WhileEnd(block_start_offset)
                block_start.jump_end = len(operations)

            else:  # pragma: nocover
                raise InvalidBlockStackValue(block_start)

        elif token.type == TokenType.WHILE:
            operation = While(None)
            block_operations_offset_stack.append(len(operations))

        elif token.type == TokenType.INTEGER:
            operation = IntPush(int(token.value))

        else:
            raise UnhandledTokenType(token)

        operations.append(operation)

    if block_operations_offset_stack:
        raise BlockStackNotEmpty

    return operations
