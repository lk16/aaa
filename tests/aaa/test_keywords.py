from pathlib import Path

import pytest

from lang.exceptions.misc import AaaParseException
from tests.aaa import check_aaa_full_source

AAA_KEYWORDS = [
    "and",
    "args",
    "as",
    "assert",
    "bool",
    "builtin_fn",
    "drop",
    "dup",
    "else",
    "false",
    "fn",
    "from",
    "if",
    "import",
    "int",
    "map",
    "nop",
    "not",
    "or",
    "over",
    "return",
    "rot",
    "str",
    "struct",
    "swap",
    "true",
    "vec",
    "while",
]


@pytest.mark.skip
def test_keywords_list_up_to_date() -> None:
    # The grammar is the only source of truth
    # So we have to compare if our list of keywords is up to date

    grammar = Path("lang/parse/aaa.lark").read_text()
    assert "|".join(sorted(AAA_KEYWORDS)) in grammar


@pytest.mark.parametrize(
    ["keyword"],
    [(keyword,) for keyword in AAA_KEYWORDS],
)
def test_keyword_invalid_param_name(keyword: str) -> None:
    code = "fn foo args " + keyword + " as int { nop }\n"
    code += "fn main { nop }"

    check_aaa_full_source(code, "", [AaaParseException])


@pytest.mark.parametrize(
    ["keyword"],
    [(keyword,) for keyword in AAA_KEYWORDS],
)
def test_keyword_valid_param_prefix(keyword: str) -> None:
    code = "fn foo args " + keyword + "_something as int { nop }\n"
    code += "fn main { nop }"

    check_aaa_full_source(code, "", [])


@pytest.mark.parametrize(
    ["keyword"],
    [(keyword,) for keyword in AAA_KEYWORDS],
)
def test_keyword_valid_member_function_name(keyword: str) -> None:
    code = "struct bar { x as int }\n"
    code += "fn bar:" + keyword + " args b as bar return bar { b }\n"
    code += "fn main { nop }"

    check_aaa_full_source(code, "", [])
