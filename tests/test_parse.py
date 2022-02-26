from parser.generic import ParseError, new_parse_generic
from typing import List, Type

import pytest

from lang.grammar import KEYWORDS, OPERATOR_KEYWORDS
from lang.parse import (
    REWRITE_RULES,
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    Identifier,
    IntegerLiteral,
    Loop,
    Operation,
    StringLiteral,
    SymbolType,
    parse,
)


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("true", True),
        ("false", True),
        ("truea", False),
        ("truefalse", False),
        ("falsetrue", False),
    ],
)
def test_parse_boolean_literal(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.BOOLEAN_LITERAL, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("1", True),
        ("0", True),
        ("00", True),
        ("1", True),
        ("9", True),
        ("123", True),
        ("-1", False),
        ("a1", False),
        ("1a", False),
    ],
)
def test_parse_integer_literal(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.INTEGER_LITERAL, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ('"', False),
        ('""', True),
        ('"aasdfasdf"', True),
        ('"\\\\"', True),
        ('"\\n"', True),
        ('"\\""', True),
        ('"asdf \\\\ asdf \\n asdf \\""', True),
    ],
)
def test_parse_string_literal(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.STRING_LITERAL, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ('"', False),
        ('""', True),
        ('"aasdfasdf"', True),
        ('"\\\\"', True),
        ('"\\n"', True),
        ('"\\""', True),
        ('"asdf \\\\ asdf \\n asdf \\""', True),
        ("1", True),
        ("123456", True),
        ("0", True),
        ("0a", False),
        ("00", True),
        ("true", True),
        ("false", True),
    ],
)
def test_parse_literal(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.LITERAL, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("a", True),
        ("0", False),
        ("/", False),
        ("z", True),
        ("_", True),
        ("A", False),
        ("Z", False),
        ("abcd_xyz", True),
        ("abcd_xyz/", False),
    ]
    + [(identifier, False) for identifier in KEYWORDS],
)
def test_parse_identifier(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.IDENTIFIER, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("foo", False),
        ("<=>", False),
    ]
    + [(op, True) for op in OPERATOR_KEYWORDS],
)
def test_parse_operation(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.OPERATION, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", True),
        ("abc", False),
        (" ", True),
        ("\n", True),
        ("  ", True),
        ("\n\n", True),
        (" \n \n", True),
        ("\n \n ", True),
        (" \na", False),
    ],
)
def test_parse_whitespace(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.WHITESPACE, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("else end", False),
        ("end", False),
        ("foo", False),
        ("if end", True),
        ("if\nend", True),
        ("if\n end", True),
        ("if a end", True),
        ("if\na\nend", True),
        ("if \na \nend", True),
        ('if \n123 true and <= "\\\\  \\n  \\" " \nend', True),
        ("if else end", True),
        ("if\nelse\nend", True),
        ("if\n else\n end", True),
        ("if a else a end", True),
        ("if\na\nelse\na\nend", True),
        ("if \na \nelse \na \nend", True),
        (
            'if \n123 true and <= "\\\\  \\n  \\" " \nelse \n123 true and <= "\\\\  \\n  \\" " \nend',
            True,
        ),
        ("if if end end", True),
        ("if if if if end end end end", True),
        ("if if else end else if else end end", True),
        ("if while else end", False),
        ("if else while end", False),
        ("if fn else end", False),
        ("if else fn end", False),
        ("if begin else end", False),
        ("if else begin end", False),
        ("if while end end", True),
        ("if while end else end", True),
        ("if else while end end", True),
        ("if substr else end", True),
        ("if else substr end", True),
    ],
)
def test_parse_branch(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.BRANCH, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("end", False),
        ("while end", True),
        ("while a end", True),
        ("while <= end", True),
        ("while true end", True),
        ("while 123 end", True),
        ("while if end end", True),
        ("while if else end end", True),
        ("while if while end else while end end end", True),
        ("while endd end", True),
    ],
)
def test_parse_loop(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.LOOP, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("end", False),
        ("while end", True),
        ("while a end", True),
        ("if end", True),
        ("if else end", True),
        ("if a else a end", True),
        ("3 5 + < 8 true >= subst substr substr", True),
        ("if while if while if while end end end end end end", True),
    ],
)
def test_parse_function_body(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.FUNCTION_BODY, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("fn a begin end", True),
        ("fn a b begin end", True),
        ("fn a b c d e f begin end", True),
        ("fn true begin end", False),
        ("fn a true begin end", False),
        ("fn a begin 3 5 < true and end", True),
        ("fn a b c begin if while end else while end end end", True),
    ],
)
def test_parse_function(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(
            REWRITE_RULES, SymbolType.FUNCTION_DEFINITION, code, SymbolType
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("", False),
        ("fn a begin end", True),
        (" fn a begin end", True),
        ("fn a begin end ", True),
        (" fn a begin end ", True),
        ("fn a begin end fn b begin end", True),
        (" fn a begin end fn b begin end ", True),
        ("fn a b c begin while end end fn d e f begin if else end end", True),
    ],
)
def test_parse_file(code: str, expected_ok: bool) -> None:
    try:
        new_parse_generic(REWRITE_RULES, SymbolType.FILE, code, SymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_function_names", "expected_arguments"],
    [
        ("fn main begin end", ["main"], [[]]),
        ("fn main a b c begin end", ["main"], [["a", "b", "c"]]),
        (
            "fn main a b c begin end fn foo d e f begin end fn bar g h i begin end",
            ["main", "foo", "bar"],
            [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]],
        ),
    ],
)
def test_file_parse_tree(
    code: str, expected_function_names: List[str], expected_arguments: List[List[str]]
) -> None:
    file = parse(code)

    assert len(file.functions) == len(expected_function_names)
    for func, expected_name, expected_args in zip(
        file.functions, expected_function_names, expected_arguments
    ):
        assert func.name == expected_name
        assert func.arguments == expected_args


@pytest.mark.parametrize(
    ["code", "expected_if_body_children", "expected_else_body_children"],
    [
        ("fn main begin if end end", 0, 0),
        ("fn main begin if 1 2 3 end end", 3, 0),
        ("fn main begin if else end end", 0, 0),
        ("fn main begin if else 1 2 3 end end", 0, 3),
        ("fn main begin if 1 2 3 else 4 5 6 end end", 3, 3),
    ],
)
def test_branch_parse_tree(
    code: str,
    expected_if_body_children: int,
    expected_else_body_children: int,
) -> None:
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions[0].body

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
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions[0].body

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
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions[0].body

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
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions[0].body

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
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions[0].body

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
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions[0].body

    assert len(func_body.items) == 1
    identifier = func_body.items[0]

    assert isinstance(identifier, Identifier)
    assert identifier.name == expected_name


@pytest.mark.parametrize(
    ["code", "expected_loop_func_body_items"],
    [
        ("fn main begin while end end", 0),
        ("fn main begin while 1 end end", 1),
        ("fn main begin while a end end", 1),
        ("fn main begin while <= end end", 1),
        ("fn main begin while <= drop end end", 2),
        ("fn main begin while sub over drop end end", 3),
        ("fn main begin while while end if end if end end end", 3),
    ],
)
def test_loop_parse_tree(code: str, expected_loop_func_body_items: int) -> None:
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions[0].body

    assert len(func_body.items) == 1
    loop = func_body.items[0]

    assert isinstance(loop, Loop)
    assert len(loop.body.items) == expected_loop_func_body_items


@pytest.mark.parametrize(
    ["code", "expected_operator"],
    [
        ("fn main begin . end", "."),
        ("fn main begin <= end", "<="),
        ("fn main begin drop end", "drop"),
        ("fn main begin over end", "over"),
    ],
)
def test_operation_parse_tree(code: str, expected_operator: str) -> None:
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions[0].body

    assert len(func_body.items) == 1
    operation = func_body.items[0]

    assert isinstance(operation, Operation)
    assert operation.operator == expected_operator
