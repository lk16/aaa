import pytest

from lang.parser.aaa import (
    KEYWORDS,
    OPERATOR_KEYWORDS,
    REWRITE_RULES,
    SymbolType,
    parse,
)
from lang.parser.generic import ParseError, new_parse_generic


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
        ("", False),
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


@pytest.mark.skip()
def test_file_parse_tree() -> None:
    code = " fn main a b c begin end "

    file = parse(code)
    assert file.symbol_type == SymbolType.FILE
    assert file.value(code) == " fn main a b c begin end "
    assert len(file.children) == 1

    func_def = file.children[0]
    assert func_def.symbol_type == SymbolType.FUNCTION_DEFINITION
    assert func_def.value(code) == "fn main a b c begin end"

    assert len(func_def.children) == 4

    expected_symbol_types = [
        SymbolType.FN,
        None,
        SymbolType.BEGIN,
        SymbolType.END,
    ]
    expected_values = [
        "fn",
        "main a b c ",
        "begin",
        "end",
    ]  # TODO remove trailing whitespace from arg list
    expected_child_counts = [0, 4, 0, 0]

    for (
        func_def_child,
        expected_symbol_type,
        expected_value,
        expected_child_count,
    ) in zip(
        func_def.children,
        expected_symbol_types,
        expected_values,
        expected_child_counts,
    ):
        assert func_def_child.symbol_type == expected_symbol_type
        assert func_def_child.value(code) == expected_value
        assert len(func_def_child.children) == expected_child_count

    fun_name_and_args = func_def.children[1]

    for child in fun_name_and_args.children:
        assert child.symbol_type == SymbolType.IDENTIFIER
        assert len(child.children) == 0

    expected_values = ["main", "a", "b", "c"]
    assert [
        child.value(code) for child in fun_name_and_args.children
    ] == expected_values


# TODO test parsetree of function with arguments
# TODO test parsetree of branch
# TODO test parsetree of identifier
# TODO test parsetree of 3 literal types
# TODO test parsetree of loop
# TODO test parsetree of operations
