#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Any, List

import click


@click.group()
def cli() -> None:
    pass


@dataclass
class Operation:
    ...


@dataclass
class PushInt(Operation):
    value: int


class PrintInt(Operation):
    ...


def parse_code(code: str) -> List[Operation]:
    operations: List[Operation] = []
    for word in code.split():
        operation: Operation
        if word == "print_int":
            operation = PrintInt()
        elif word.isdigit():
            operation = PushInt(int(word))
        else:
            raise ValueError(f"Syntax error: can't handle '{code}'")
        operations.append(operation)

    return operations


def simulate_program(operations: List[Operation]) -> None:
    next_operation_index = 0
    stack: List[Any] = []

    while next_operation_index < len(operations):
        operation = operations[next_operation_index]
        if isinstance(operation, PushInt):
            stack.append(operation.value)
            next_operation_index += 1
        elif isinstance(operation, PrintInt):
            value = stack.pop()
            print(value)
            next_operation_index += 1
        else:
            raise ValueError(f"Unhandled operation {type(operation)}")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
def run(file: str) -> None:
    with open(file, "r") as f:
        program = f.read()
    operations = parse_code(program)
    simulate_program(operations)


if __name__ == "__main__":
    cli()
