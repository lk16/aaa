import json
import re
from typing import List

import pytest

from lang.tokenize import simple_tokens


@pytest.fixture
def aaa_text_mate_patterns() -> List[re.Pattern[str]]:
    syntax_json = json.load(open("./aaa-vscode-extension/syntaxes/aaa.tmLanguage.json"))

    patterns: List[re.Pattern[str]] = []

    for pattern in syntax_json["patterns"]:
        if "match" in pattern:
            patterns.append(re.compile(pattern["match"]))

    for repo_item in syntax_json["repository"].values():
        if "patterns" in repo_item:
            for pattern in repo_item["patterns"]:
                if "match" in pattern:
                    patterns.append(re.compile(pattern["match"]))
        if "match" in repo_item:
            patterns.append(re.compile(repo_item["match"]))

    return patterns


@pytest.mark.parametrize(
    ["token_str"], [(token_pair[0],) for token_pair in simple_tokens]
)
def test_extension_recoginizes_simple_token(
    token_str: str, aaa_text_mate_patterns: List[re.Pattern[str]]
) -> None:
    assert any(pattern.match(token_str) for pattern in aaa_text_mate_patterns)
