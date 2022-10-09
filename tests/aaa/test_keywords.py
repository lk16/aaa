import pytest

from aaa.cross_referencer.cross_referencer import AAA_KEYWORDS
from aaa.cross_referencer.exceptions import KeywordUsedAsIdentifier
from tests.aaa import check_aaa_full_source


@pytest.mark.parametrize(
    ["keyword"],
    [(keyword,) for keyword in AAA_KEYWORDS],
)
def test_keyword_invalid_param_name(keyword: str) -> None:
    code = "fn foo args " + keyword + " as int { nop }\n"
    code += "fn main { nop }"

    check_aaa_full_source(code, "", [KeywordUsedAsIdentifier])


@pytest.mark.parametrize(
    ["keyword"],
    [(keyword,) for keyword in AAA_KEYWORDS],
)
def test_keyword_invalid_function_name(keyword: str) -> None:
    code = "fn " + keyword + " { nop }\n"
    code += "fn main { nop }"

    check_aaa_full_source(code, "", [KeywordUsedAsIdentifier])


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
