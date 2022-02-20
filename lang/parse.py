from itertools import count
from typing import Dict, List, Tuple

from lang.exceptions import (
    InvalidBlockStackValue,
    InvalidJump,
    UnexpectedEndOfFile,
    UnexpectedToken,
    UnhandledTokenType,
)
from lang.program import Program
from lang.tokenize import Token, TokenType
from lang.types import (
    And,
    BoolPush,
    CharNewLinePrint,
    Divide,
    Drop,
    Dup,
    Else,
    End,
    Equals,
    Function,
    If,
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
    Operation,
    Or,
    Over,
    Plus,
    Print,
    Rot,
    StringLength,
    StringPush,
    SubString,
    Swap,
    While,
    WhileEnd,
)


def parse(tokens: List[Token]) -> Program:
    functions: Dict[str, Function] = {}

    token_offset = 0
    while token_offset < len(tokens):
        token = tokens[token_offset]

        if token.type == TokenType.FUNCTION:
            function, consumed_tokens = parse_function(tokens[token_offset:])
            functions[function.name] = function
            token_offset += consumed_tokens

        elif token.type == TokenType.COMMENT:
            token_offset += 1

        else:
            raise UnexpectedToken(token)

    return Program(functions)


def parse_function(
    tokens: List[Token],
) -> Tuple[Function, int]:  # noqa: C901  # Allow high complexity

    # TODO IndexErrors can happen anywhere in this function

    if tokens[1].type != TokenType.IDENTIFIER:
        raise UnexpectedToken(tokens[1])

    name = tokens[1].value
    # TODO check that the name of the function is not taken already

    arg_names: List[str] = []

    for arg_offset in count():
        arg_token = tokens[1 + arg_offset]

        if arg_token.type == TokenType.IDENTIFIER:
            # TODO check that the argument does not overlap with other args or function names
            arg_names.append(arg_token.value)
        elif arg_token.type == TokenType.FUNCTION_BEGIN:
            break
        else:
            raise UnexpectedToken(arg_token)

    arg_count = len(arg_names)

    operations, consumed_body_tokens = parse_function_body(tokens[2 + arg_count + 1 :])

    function = Function(name, arg_count, operations)
    consumed_tokens = 2 + arg_count + 1 + consumed_body_tokens + 1

    return function, consumed_tokens


def parse_function_body(  # noqa: C901  # Allow high complexity
    tokens: List[Token],
) -> Tuple[List[Operation], int]:  # noqa: C901 # Allow high complexity
    operations: List[Operation] = []

    # Stack of indexes in block start operations (such as If) in the operations list
    block_operations_offset_stack: List[int] = []

    for consumed_tokens, token in enumerate(tokens):
        operation: Operation

        simple_tokens: Dict[TokenType, Operation] = {
            TokenType.PLUS: Plus(),
            TokenType.MINUS: Minus(),
            TokenType.STAR: Multiply(),
            TokenType.SLASH: Divide(),
            TokenType.PERCENT: Modulo(),
            TokenType.TRUE: BoolPush(True),
            TokenType.FALSE: BoolPush(False),
            TokenType.AND: And(),
            TokenType.OR: Or(),
            TokenType.NOT: Not(),
            TokenType.EQUAL: Equals(),
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
            TokenType.SUBSTRING: SubString(),
            TokenType.STRING_LENGTH: StringLength(),
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
                raise UnexpectedToken(token) from e

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
            except IndexError:
                # This is the end of the function

                # The block operations stack is empty so all jumps should be initialized to some "address" integer value.
                for operation in operations:
                    if any(
                        [
                            isinstance(operation, If)
                            and operation.jump_if_false is None,
                            isinstance(operation, Else) and operation.jump_end is None,
                            isinstance(operation, While) and operation.jump_end is None,
                        ]
                    ):
                        raise InvalidJump  # pragma: nocover

                return operations, consumed_tokens

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

        elif token.type == TokenType.STRING:
            string = (
                token.value[1:-1]
                .replace("\\n", "\n")
                .replace('\\"', '"')
                .replace("\\\\", "\\")
            )
            operation = StringPush(string)

        elif token.type == TokenType.COMMENT:
            continue  # Comments obviously don't do anything

        elif token.type == TokenType.FUNCTION:
            raise NotImplementedError

        elif token.type == TokenType.FUNCTION_BEGIN:
            raise NotImplementedError  # This probably doesn't have to do anything

        else:
            raise UnhandledTokenType(token)

        operations.append(operation)

    raise UnexpectedEndOfFile
