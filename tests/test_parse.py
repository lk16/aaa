from parser.parser.exceptions import ParseError
from parser.parser.models import Tree
from parser.parser.parser import Parser
from parser.tokenizer.models import Token
from parser.tokenizer.tokenizer import Tokenizer
from typing import List, Tuple, Type

import pytest

from lang.grammar.parser import (
    NON_TERMINAL_RULES,
    PRUNED_NON_TERMINALS,
    PRUNED_TERMINALS,
    TERMINAL_RULES,
    Terminal,
)
from lang.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    Identifier,
    IntegerLiteral,
    Operator,
    StringLiteral,
    parse,
)


def parse_as(code: str, non_terminal_name: str) -> Tuple[List[Token], Tree]:
    filename = "foo.txt"

    tokens = Tokenizer(
        filename=filename,
        code=code,
        terminal_rules=TERMINAL_RULES,
        pruned_terminals=PRUNED_TERMINALS,
    ).tokenize()

    tree = Parser(
        filename=filename,
        tokens=tokens,
        code=code,
        non_terminal_rules=NON_TERMINAL_RULES,
        pruned_non_terminals=PRUNED_NON_TERMINALS,
        root_token=non_terminal_name,
    ).parse()

    return tokens, tree


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("true", True),
        ("false", True),
        ("truea", False),
        ("truefalse", False),
        ("falsetrue", False),
    ],
)
def test_parse_boolean_literal(code: str, expected_ok: bool) -> None:
    try:
        parse_as(code, "BOOLEAN")
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


def test_parse_string_non_greedy() -> None:
    code = '"a" "b"'
    tokens, tree = parse_as(code, "FUNCTION_BODY")
    assert len(tree.children) == 2
    a, b = tree.children

    assert a.value(tokens, code) == '"a"'
    assert a.token_type == Terminal.STRING

    assert b.value(tokens, code) == '"b"'
    assert b.token_type == Terminal.STRING


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("else nop end", False),
        ("end", False),
        ("foo", False),
        ("if true begin nop end", True),
        ("if\ntrue\nbegin\nnop\nend", True),
        ("if\n true\n begin\n nop\n end", True),
        ("if true begin a end", True),
        ("if true begin\na\nend", True),
        ("if \ntrue \nbegin \na \nend", True),
        ('if \ntrue begin 123 true and <= "\\\\  \\n  \\" " \nend', True),
        ("if nop begin nop else nop end", True),
        ("if\nnop\nbegin\nnop\nelse\nnop\nend", True),
        ("if\n nop\n begin\n nop\n else\n nop\n end", True),
        ("if a begin a else a end", True),
        ("if\na\nbegin\na\nelse\na\nend", True),
        ("if \na \nbegin \nnop \nelse \na \nend", True),
        (
            'if \nnop begin 123 true and <= "\\\\  \\n  \\" " \nelse \n123 true and <= "\\\\  \\n  \\" " \nend',
            True,
        ),
        ("if nop begin if nop begin nop end end", True),
        (
            "if nop begin if nop begin if nop begin if nop begin nop end end end end",
            True,
        ),
        (
            "if nop begin if nop begin nop else nop end else if nop begin nop else nop end end",
            True,
        ),
        ("if nop begin while nop begin else nop end", False),
        ("if nop begin nop else while nop end", False),
        ("if fn else nop end", False),
        ("if nop else fn end", False),
        ("if nop begin nop else nop end", True),
        ("if begin nop else nop end", False),
        ("if nop begin else nop end", False),
        ("if nop begin nop else end", False),
        ("if nop begin nop else begin nop end", False),
        ("if nop begin while nop begin nop end end", True),
        ("if nop begin while nop begin nop end else nop end", True),
        ("if substr begin nop else nop end", True),
        ("if nop begin nop else substr end", True),
    ],
)
def test_parse_branch(code: str, expected_ok: bool) -> None:
    try:
        parse_as(code, "BRANCH")
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("end", False),
        ("while nop begin nop end", True),
        ("while nop begin a end", True),
        ("while <= begin nop end", True),
        ("while true begin nop end", True),
        ("while 123 begin nop end", True),
        ("while nop begin if nop begin nop end end", True),
        ("while nop begin if nop begin nop else nop end end", True),
        (
            "while nop begin if nop begin while nop begin nop end else while nop begin nop end end end",
            True,
        ),
        ("while nop begin nop endd end", True),
    ],
)
def test_parse_loop(code: str, expected_ok: bool) -> None:
    try:
        parse_as(code, "LOOP")
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("end", False),
        ("while nop begin nop end", True),
        ("while nop begin a end", True),
        ("if nop begin nop end", True),
        ("if nop begin nop else nop end", True),
        ("if nop begin a else a end", True),
        ("3 5 + < 8 true >= substr substr substr", True),
        (
            "if nop begin while nop begin if nop begin while nop begin if nop begin while nop begin nop end end end end end end",
            True,
        ),
    ],
)
def test_parse_function_body(code: str, expected_ok: bool) -> None:
    try:
        parse_as(code, "FUNCTION_BODY")
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("fn a begin nop end", True),
        ("fn a args begin nop end", False),
        ("fn a return begin nop end", False),
        ("fn a args return begin nop end", False),
        ("fn a args b as int begin nop end", True),
        ("fn a args b as int, c as int begin nop end", True),
        ("fn a return int begin nop end", True),
        ("fn a return int, int begin nop end", True),
        ("fn a args b as int, c as int return int, int begin nop end", True),
        (
            "fn a args b as int, c as int return int, int begin if true begin nop end end",
            True,
        ),
    ],
)
def test_parse_function(code: str, expected_ok: bool) -> None:
    try:
        parse_as(code, "FUNCTION_DEFINITION")
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_if_body_children", "expected_else_body_children"],
    [
        ("fn main begin if nop begin nop end end", 1, 0),
        ("fn main begin if nop begin 1 2 3 end end", 3, 0),
        ("fn main begin if nop begin nop else nop end end", 1, 1),
        ("fn main begin if nop begin nop else 1 2 3 end end", 1, 3),
        ("fn main begin if nop begin 1 2 3 else 4 5 6 end end", 3, 3),
    ],
)
def test_branch_parse_tree(
    code: str,
    expected_if_body_children: int,
    expected_else_body_children: int,
) -> None:
    file = parse("foo.txt", code)
    assert len(file.functions) == 1
    func_body = file.functions["main"].body

    assert len(func_body.items) == 1
    branch = func_body.items[0]

    assert isinstance(branch, Branch)
    assert len(branch.if_body.items) == expected_if_body_children
    assert len(branch.else_body.items) == expected_else_body_children


@pytest.mark.parametrize(
    ["code", "expected_type"],
    [
        ("fn main begin 1 end", IntegerLiteral),
        ("fn main begin true end", BooleanLiteral),
        ('fn main begin "foo bar" end', StringLiteral),
    ],
)
def test_literal_parse_tree(code: str, expected_type: Type[AaaTreeNode]) -> None:
    file = parse("foo.txt", code)
    assert len(file.functions) == 1
    func_body = file.functions["main"].body

    assert len(func_body.items) == 1
    identifier = func_body.items[0]

    assert isinstance(identifier, expected_type)


@pytest.mark.parametrize(
    ["code", "expected_value"],
    [
        ("fn main begin false end", False),
        ("fn main begin true end", True),
    ],
)
def test_boolean_literal_parse_tree(code: str, expected_value: bool) -> None:
    file = parse("foo.txt", code)
    assert len(file.functions) == 1
    func_body = file.functions["main"].body

    assert len(func_body.items) == 1
    bool_lit = func_body.items[0]

    assert isinstance(bool_lit, BooleanLiteral)
    assert bool_lit.value == expected_value


@pytest.mark.parametrize(
    ["code", "expected_value"],
    [
        ("fn main begin 1 end", 1),
        ("fn main begin 123456789 end", 123456789),
        ("fn main begin 0 end", 0),
        ("fn main begin 007 end", 7),
        ("fn main begin 0017 end", 17),
    ],
)
def test_integer_literal_parse_tree(code: str, expected_value: int) -> None:
    file = parse("foo.txt", code)
    assert len(file.functions) == 1
    func_body = file.functions["main"].body

    assert len(func_body.items) == 1
    int_lit = func_body.items[0]

    assert isinstance(int_lit, IntegerLiteral)
    assert int_lit.value == expected_value


@pytest.mark.parametrize(
    ["code", "expected_value"],
    [
        ('fn main begin "" end', ""),
        ('fn main begin "foo" end', "foo"),
        ('fn main begin "foo bar" end', "foo bar"),
        ('fn main begin " \\" \\\\ \\n " end', ' " \\ \n '),
    ],
)
def test_string_literal_parse_tree(code: str, expected_value: str) -> None:
    file = parse("foo.txt", code)
    assert len(file.functions) == 1
    func_body = file.functions["main"].body

    assert len(func_body.items) == 1
    str_lit = func_body.items[0]

    assert isinstance(str_lit, StringLiteral)
    assert str_lit.value == expected_value


@pytest.mark.parametrize(
    ["code", "expected_name"],
    [
        ("fn main begin a end", "a"),
        ("fn main begin z end", "z"),
        ("fn main begin _ end", "_"),
        ("fn main begin azabc end", "azabc"),
        ("fn main begin foobar_asdfczc end", "foobar_asdfczc"),
    ],
)
def test_identifier_parse_tree(code: str, expected_name: str) -> None:
    file = parse("foo.txt", code)
    assert len(file.functions) == 1
    func_body = file.functions["main"].body

    assert len(func_body.items) == 1
    identifier = func_body.items[0]

    assert isinstance(identifier, Identifier)
    assert identifier.name == expected_name


@pytest.mark.parametrize(
    ["code", "expected_operator"],
    [
        ("fn main begin . end", "."),
        ("fn main begin <= end", "<="),
        ("fn main begin drop end", "drop"),
        ("fn main begin over end", "over"),
    ],
)
def test_operator_parse_tree(code: str, expected_operator: str) -> None:
    file = parse("foo.txt", code)
    assert len(file.functions) == 1
    func_body = file.functions["main"].body

    assert len(func_body.items) == 1
    operator = func_body.items[0]

    assert isinstance(operator, Operator)
    assert operator.value == expected_operator
