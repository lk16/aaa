from parser.exceptions import ParseError
from parser.parser import parse_generic
from typing import List, Type

import pytest

from lang.grammar.parser import (
    HARD_PRUNED_SYMBOL_TYPES,
    REWRITE_RULES,
    SOFT_PRUNED_SYMBOL_TYPES,
)
from lang.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    Identifier,
    IntegerLiteral,
    Operator,
    StringLiteral,
    SymbolType,
    parse,
)


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
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "BOOLEAN_LITERAL",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
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
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "INTEGER_LITERAL",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
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
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "STRING_LITERAL",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


def test_parse_string_non_greedy() -> None:
    code = '"a" "b"'
    tree = parse_generic(
        REWRITE_RULES,
        code,
        HARD_PRUNED_SYMBOL_TYPES,
        SOFT_PRUNED_SYMBOL_TYPES,
        "FUNCTION_BODY",
    )
    assert len(tree.children) == 2
    a, b = tree.children

    assert a.value(code) == '"a"'
    assert a.token_type == SymbolType.STRING_LITERAL

    assert b.value(code) == '"b"'
    assert b.token_type == SymbolType.STRING_LITERAL


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
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
    + [(identifier, False) for identifier in get_operator_keywords()],
)
def test_parse_identifier(code: str, expected_ok: bool) -> None:
    try:
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "IDENTIFIER",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("foo", False),
        ("<=>", False),
    ]
    + [(op, True) for op in get_operator_keywords()],
)
def test_parse_operator(code: str, expected_ok: bool) -> None:
    try:
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "OPERATOR",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
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
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES - {SymbolType.WHITESPACE},
            SOFT_PRUNED_SYMBOL_TYPES,
            "WHITESPACE",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


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
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "BRANCH",
        )
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
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "LOOP",
        )
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
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "FUNCTION_BODY",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("fn a begin nop end", True),
        ("fn a b begin nop end", True),
        ("fn a b c d e f begin nop end", True),
        ("fn true begin nop end", False),
        ("fn a true begin nop end", False),
        ("fn a begin 3 5 < true and end", True),
        (
            "fn a b c begin if nop begin while nop begin nop end else while nop begin nop end end end",
            True,
        ),
    ],
)
def test_parse_function(code: str, expected_ok: bool) -> None:
    try:
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "FUNCTION_DEFINITION",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "expected_ok"],
    [
        ("fn a begin nop end", True),
        (" fn a begin nop end", True),
        ("fn a begin nop end ", True),
        (" fn a begin nop end ", True),
        ("fn a begin nop end fn b begin nop end", True),
        (" fn a begin nop end fn b begin nop end ", True),
        (
            "fn a b c begin while nop begin nop end end fn d e f begin if nop begin nop else nop end end",
            True,
        ),
    ],
)
def test_parse_file(code: str, expected_ok: bool) -> None:
    try:
        parse_generic(
            REWRITE_RULES,
            code,
            HARD_PRUNED_SYMBOL_TYPES,
            SOFT_PRUNED_SYMBOL_TYPES,
            "ROOT",
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    ["code", "func_names", "expected_arguments"],
    [
        ("fn main begin nop end", ["main"], [[]]),
        ("fn main a b c begin nop end", ["main"], [["a", "b", "c"]]),
        (
            "fn main a b c begin nop end fn foo d e f begin nop end fn bar g h i begin nop end",
            ["main", "foo", "bar"],
            [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]],
        ),
    ],
)
def test_file_parse_tree(
    code: str, func_names: List[str], expected_arguments: List[List[str]]
) -> None:
    file = parse(code)

    assert len(file.functions) == len(func_names)
    for func_name, expected_args in zip(func_names, expected_arguments):
        func = file.functions[func_name]
        assert func.name == func_name
        assert func.arguments == expected_args


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
    file = parse(code)
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
    file = parse(code)
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
    file = parse(code)
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
    file = parse(code)
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
    file = parse(code)
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
    file = parse(code)
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
    file = parse(code)
    assert len(file.functions) == 1
    func_body = file.functions["main"].body

    assert len(func_body.items) == 1
    operator = func_body.items[0]

    assert isinstance(operator, Operator)
    assert operator.value == expected_operator
