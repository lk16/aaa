import pytest

from lang.tokenizer.aaa import REWRITE_RULES, SymbolType
from lang.tokenizer.generic import new_tokenize_generic


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
    tree = new_tokenize_generic(
        REWRITE_RULES, SymbolType.BOOLEAN_LITERAL, code, SymbolType
    )
    assert bool(tree) == expected_ok


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
    tree = new_tokenize_generic(
        REWRITE_RULES, SymbolType.INTEGER_LITERAL, code, SymbolType
    )
    assert bool(tree) == expected_ok


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
    tree = new_tokenize_generic(
        REWRITE_RULES, SymbolType.STRING_LITERAL, code, SymbolType
    )
    assert bool(tree) == expected_ok


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
    tree = new_tokenize_generic(REWRITE_RULES, SymbolType.LITERAL, code, SymbolType)
    assert bool(tree) == expected_ok


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
    ],
)
def test_parse_identifier(code: str, expected_ok: bool) -> None:
    tree = new_tokenize_generic(REWRITE_RULES, SymbolType.IDENTIFIER, code, SymbolType)
    assert bool(tree) == expected_ok


# TODO def test_parse_operation()
# TODO def test_parse_branch()
# TODO def test_parse_loop()
# TODO def test_parse_function_body()
# TODO def test_parse_function()
# TODO def test_parse_program()

# TODO test comments in every possible place
# TODO test whitespace in every possible place
