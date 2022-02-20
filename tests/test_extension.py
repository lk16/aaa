import json
import re
from typing import Dict, List

import pytest

from lang.tokenize import NON_SIMPLE_TOKEN_TYPES, SIMPLE_TOKENS, TokenType


@pytest.fixture
def aaa_text_mate_patterns() -> List[re.Pattern[str]]:
    syntax_json = json.load(open("./aaa-vscode-extension/syntaxes/aaa.tmLanguage.json"))

    patterns: List[re.Pattern[str]] = []

    for pattern in syntax_json["patterns"]:
        if "match" in pattern:
            patterns.append(re.compile(pattern["match"]))

    for repo_item in syntax_json["repository"].values():
        for pattern in repo_item.get("patterns", []):
            if "match" in pattern:
                patterns.append(re.compile(pattern["match"]))

        if "match" in repo_item:
            patterns.append(re.compile(repo_item["match"]))

    return patterns


@pytest.mark.parametrize(
    ["token_str"], [(token_pair[0],) for token_pair in SIMPLE_TOKENS]
)
def test_extension_recoginizes_simple_token(
    token_str: str, aaa_text_mate_patterns: List[re.Pattern[str]]
) -> None:
    assert any(pattern.match(token_str) for pattern in aaa_text_mate_patterns)


@pytest.fixture
def non_simple_token_test_values() -> Dict[TokenType, List[str]]:
    return {
        TokenType.COMMENT: ["//", "// abc"],
        TokenType.INTEGER: ["0", "123", "123456789"],
        TokenType.STRING: [],  # TODO test elsewhere. This is complicated due to escape sequences
    }


@pytest.mark.parametrize(
    ["non_simple_token_type"], [(token_type,) for token_type in NON_SIMPLE_TOKEN_TYPES]
)
def test_extension_recoginizes_non_simple_token(
    non_simple_token_test_values: Dict[TokenType, List[str]],
    aaa_text_mate_patterns: List[re.Pattern[str]],
    non_simple_token_type: TokenType,
) -> None:
    assert non_simple_token_type in non_simple_token_test_values

    token_strings = non_simple_token_test_values[non_simple_token_type]

    for token_str in token_strings:
        assert any(pattern.match(token_str) for pattern in aaa_text_mate_patterns)
