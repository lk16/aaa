from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir

import pytest

from aaa.formatter import AaaFormatter


def format_aaa_source(code: str) -> str:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name
    file.write_text(code)
    return AaaFormatter(file).get_formatted()


def format_aaa_builtins(code: str) -> str:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name
    file.write_text(code)
    return AaaFormatter(file).get_formatted(force_parse_as_builtins_file=True)


def test_format_empty_file() -> None:
    # Empty files don't get a trailing whitespace
    assert "" == format_aaa_source("")


# TODO prevent string reformatting in this file


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        ('from "a" import b\n', 'from "a" import b'),
        ('from "a" import b\n', 'from "a" import b    '),
        ('from "a" import b\n', '    from "a" import b'),
        ('from "a" import b\n', '\tfrom\n"a"    import b\t'),
        ('from "a" import b, c\n', 'from "a" import b from "a" import c'),
        ('from "a" import b, c\n', 'from "a" import c from "a" import b'),
        (
            'from "a" import\n'
            + "    aaaaaaaaa as bbbbbbbbb,\n"
            + "    ccccccccc as ddddddddd,\n"
            + "    eeeeeeeee as fffffffff,\n"
            + "    ggggggggg,\n",
            'from "a" import aaaaaaaaa as bbbbbbbbb, ccccccccc as ddddddddd, eeeeeeeee as fffffffff, ggggggggg',
        ),
    ],
)
def test_format_imports(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        ("struct Foo {}\n", "struct Foo { }"),
        ("struct Foo {\n    value as int,\n}\n", "struct Foo { value as int }"),
        (
            "struct Foo {\n    func as fn[int][bool],\n}\n",
            "struct Foo { func as fn [ int ] [ bool ] }",
        ),
    ],
)
def test_format_struct(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        ("enum Foo {\n    value as int,\n}\n", "enum Foo { value as int }"),
        ("enum Foo {\n    value as int,\n}\n", "enum Foo { value as { int } }"),
        (
            "enum Foo {\n    value as { int, bool },\n}\n",
            "enum Foo { value as { int, bool } }",
        ),
        (
            "enum Foo {\n"
            + "    value as {\n"
            + "        int,\n"
            + "        bool,\n"
            + "        VeryLongStructType,\n"
            + "        VeryLongStructType,\n"
            + "        VeryLongStructType,\n"
            + "        VeryLongStructType,\n"
            + "    }\n"
            + "}\n",
            "enum Foo { value as { int, bool, VeryLongStructType, VeryLongStructType, VeryLongStructType, VeryLongStructType } }",
        ),
        ("enum Foo {\n    value,\n}\n", "enum Foo { value }"),
    ],
)
def test_format_enum(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        ("fn foo\n", "fn foo"),
        ("fn foo args bar as int\n", "fn foo args bar as int"),
        ("fn foo args bar as const int\n", "fn foo args bar as const int"),
        (
            "fn foo args bar as int, bar as int\n",
            "fn foo args bar as int , bar as int",
        ),
        ("fn foo return int\n", "fn foo return int"),
        ("fn foo return int, int\n", "fn foo return int , int"),
        ("fn foo[T]\n", "fn foo [ T ]"),
        (
            "fn Bar:foo args bar as Bar return int\n",
            "fn Bar : foo args bar as Bar return int",
        ),
        (
            "fn foo args foo as int return never\n",
            "fn foo args foo as int return never",
        ),
        (
            "fn foo\n"
            + "    args a as VeryLongStructType, b as VeryLongStructType, c as VeryLongStructType\n"
            + "    return int\n",
            "fn foo args a as VeryLongStructType, b as VeryLongStructType, c as VeryLongStructType return int",
        ),
        (
            "fn foo\n"
            + "    args\n"
            + "        a as VeryLongStructType,\n"
            + "        b as VeryLongStructType,\n"
            + "        c as VeryLongStructType,\n"
            + "        d as VeryLongStructType,\n"
            + "    return int\n",
            "fn foo args a as VeryLongStructType, b as VeryLongStructType, c as VeryLongStructType, d as VeryLongStructType return int",
        ),
        (
            "fn foo\n"
            + "    args a as int\n"
            + "    return VeryLongStructType, VeryLongStructType, VeryLongStructType, int\n",
            "fn foo args a as int return VeryLongStructType, VeryLongStructType, VeryLongStructType, int",
        ),
        (
            "fn foo\n"
            + "    args a as int\n"
            + "    return\n"
            + "        VeryLongStructType,\n"
            + "        VeryLongStructType,\n"
            + "        VeryLongStructType,\n"
            + "        VeryLongStructType,\n",
            "fn foo args a as int return VeryLongStructType, VeryLongStructType, VeryLongStructType, VeryLongStructType",
        ),
    ],
)
def test_format_function_declaration(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_builtins(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n    3\n}\n",
            "fn foo { 3 }",
        ),
        (
            "fn foo {\n    false\n}\n",
            "fn foo { false }",
        ),
        (
            'fn foo {\n    "Hello world"\n}\n',
            'fn foo { "Hello world" }',
        ),
        (
            "fn foo {\n    call\n}\n",
            "fn foo { call }",
        ),
        (
            "fn foo {\n    return\n}\n",
            "fn foo { return }",
        ),
        (
            'fn foo {\n    "foo" fn\n}\n',
            'fn foo { "foo" fn }',
        ),
        (
            'fn foo {\n    "foo" ?\n}\n',
            'fn foo { "foo" ? }',
        ),
    ],
)
def test_format_function_simple(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n    3 false\n}\n",
            "fn foo { 3 false }",
        ),
        (
            "fn foo {\n    3\n    false\n}\n",
            "fn foo { 3\nfalse }",
        ),
        (
            "fn foo {\n    3\n\n    false\n}\n",
            "fn foo { 3\n\nfalse }",
        ),
        (
            "fn foo {\n    3\n\n    false\n}\n",
            "fn foo { 3\n\n\nfalse }",
        ),
        (
            "fn foo {\n"
            + "    3\n"
            + "    if true {\n"
            + "        nop\n"
            + "    }\n"
            + "}\n",
            "fn foo { 3 if true { nop } }",
        ),
        (
            "fn foo {\n"
            + "    3\n"
            + "    if true {\n"
            + "        nop\n"
            + "    }\n"
            + "}\n",
            "fn foo { 3\nif true { nop } }",
        ),
        (
            "fn foo {\n"
            + "    3\n"
            + "\n"
            + "    if true {\n"
            + "        nop\n"
            + "    }\n"
            + "}\n",
            "fn foo { 3\n\nif true { nop } }",
        ),
    ],
)
def test_format_function_body_newlines(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n    x <- { 3 }\n}\n",
            "fn foo { x <- { 3 } }",
        ),
        (
            "fn foo {\n    x, y <- { 3 4 }\n}\n",
            "fn foo { x , y <- { 3 4 } }",
        ),
        (
            "fn foo {\n"
            + "    x, y <- {\n"
            + "        if true {\n"
            + "            nop\n"
            + "        }\n"
            + "    }\n"
            + "}\n",
            "fn foo { x , y <- { if true { nop } } }",
        ),
    ],
)
def test_format_function_with_assignment(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n" + "    if true {\n" + "        nop\n" + "    }\n" + "}\n",
            "fn foo { if true { nop } }",
        ),
        (
            "fn foo {\n"
            + "    if\n"
            + "        very_long_function very_long_function very_long_function very_long_function\n"
            + "        very_long_function\n"
            + "    {\n"
            + "        nop\n"
            + "    }\n"
            + "}\n",
            "fn foo { if very_long_function very_long_function very_long_function very_long_function very_long_function { nop } }",
        ),
        (
            "fn foo {\n"
            + "    if true {\n"
            + "        nop\n"
            + "    } else {\n"
            + "        nop\n"
            + "    }\n"
            + "}\n",
            "fn foo { if true { nop } else { nop } }",
        ),
        (
            "fn foo {\n"
            + "    if\n"
            + "        very_long_function very_long_function very_long_function very_long_function\n"
            + "        very_long_function\n"
            + "    {\n"
            + "        nop\n"
            + "    } else {\n"
            + "        nop\n"
            + "    }\n"
            + "}\n",
            "fn foo { if very_long_function very_long_function very_long_function very_long_function very_long_function { nop } else { nop } }",
        ),
    ],
)
def test_format_function_with_branch(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n" + "    foreach {\n" + "        nop\n" + "    }\n" + "}\n",
            "fn foo { foreach { nop } }",
        ),
    ],
)
def test_format_function_with_foreach(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n" + "    foo\n" + "}\n",
            "fn foo { foo }",
        ),
        (
            "fn foo {\n" + "    foo[T]\n" + "}\n",
            "fn foo { foo [ T ] }",
        ),
        (
            "fn foo {\n" + "    bar:foo\n" + "}\n",
            "fn foo { bar : foo }",
        ),
    ],
)
def test_format_function_with_function_call(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n" + "    fn[][]\n" + "}\n",
            "fn foo { fn [ ] [ ] }",
        ),
        (
            "fn foo {\n" + "    fn[][never]\n" + "}\n",
            "fn foo { fn [ ] [ never ] }",
        ),
        (
            "fn foo {\n" + "    fn[][int]\n" + "}\n",
            "fn foo { fn [ ] [ int ] }",
        ),
        (
            "fn foo {\n" + "    fn[int, int][str, str]\n" + "}\n",
            "fn foo { fn [ int , int ] [ str, str ] }",
        ),
    ],
)
def test_format_function_with_function_type_literal(
    code: str, expected_format: str
) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n"
            + "    match {\n"
            + "        case Foo:bar { nop }\n"
            + "        default { nop }\n"
            + "    }\n"
            + "}\n",
            "fn foo { match { case Foo:bar { nop } default { nop } } }",
        ),
        (
            "fn foo {\n"
            + "    match {\n"
            + "        case Foo:bar {\n"
            + "            very_long_function very_long_function very_long_function\n"
            + "            very_long_function\n"
            + "        }\n"
            + "        default {\n"
            + "            very_long_function very_long_function very_long_function\n"
            + "            very_long_function\n"
            + "        }\n"
            + "    }\n"
            + "}\n",
            "fn foo { match { case Foo:bar { "
            + "very_long_function very_long_function very_long_function very_long_function "
            + "} default { "
            + " very_long_function very_long_function very_long_function very_long_function "
            + "} } }",
        ),
        (
            "fn foo {\n"
            + "    match {\n"
            + "        case Foo:bar as foo, foo, foo { nop }\n"
            + "    }\n"
            + "}\n",
            "fn foo { match { case Foo:bar as foo , foo, foo { nop } } }",
        ),
        (
            "fn foo {\n"
            + "    match {\n"
            + "        case Foo:bar {\n"
            + "            if true {\n"
            + "                nop\n"
            + "            }\n"
            + "        }\n"
            + "    }\n"
            + "}\n",
            "fn foo { match { case Foo:bar { if true { nop } } } }",
        ),
        (
            "fn foo {\n"
            + "    match {\n"
            + "        default {\n"
            + "            if true {\n"
            + "                nop\n"
            + "            }\n"
            + "        }\n"
            + "    }\n"
            + "}\n",
            "fn foo { match { default { if true { nop } } } }",
        ),
    ],
)
def test_format_function_with_match(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n" + '    foo "foo" { 3 } !\n' + "}\n",
            'fn foo { foo "foo" { 3 } ! }',
        ),
        (
            "fn foo {\n"
            + "    foo\n"
            + '    "foo" {\n'
            + "        very_long_function very_long_function very_long_function very_long_function\n"
            + "        very_long_function\n"
            + "    } !\n"
            + "}\n",
            'fn foo { foo "foo" { very_long_function very_long_function very_long_function very_long_function very_long_function } ! }',
        ),
        (
            "fn foo {\n"
            + '    foo "foo" {\n'
            + "        if true {\n"
            + "            nop\n"
            + "        }\n"
            + "    } !\n"
            + "}\n",
            'fn foo { foo "foo" { if true { nop } } ! }',
        ),
    ],
)
def test_format_function_with_struct_field_update(
    code: str, expected_format: str
) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n" + "    use x {\n" + "        nop\n" + "    }\n" + "}\n",
            "fn foo { use x { nop } }",
        ),
        (
            "fn foo {\n"
            + "    use\n"
            + "        very_long_var_name,\n"
            + "        very_long_var_name,\n"
            + "        very_long_var_name,\n"
            + "        very_long_var_name,\n"
            + "    {\n"
            + "        nop\n"
            + "    }\n"
            + "}\n",
            "fn foo { use very_long_var_name, very_long_var_name, very_long_var_name, very_long_var_name { nop } }",
        ),
    ],
)
def test_format_function_with_use_block(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)


@pytest.mark.parametrize(
    ["expected_format", "code"],
    [
        (
            "fn foo {\n" + "    while true {\n" + "        nop\n" + "    }\n" + "}\n",
            "fn foo { while true { nop } }",
        ),
        (
            "fn foo {\n"
            + "    while\n"
            + "        if true {\n"
            + "            nop\n"
            + "        }\n"
            + "    {\n"
            + "        nop\n"
            + "    }\n"
            + "}\n",
            "fn foo { while if true { nop } { nop } }",
        ),
    ],
)
def test_format_function_with_while_loop(code: str, expected_format: str) -> None:
    assert expected_format == format_aaa_source(code)
