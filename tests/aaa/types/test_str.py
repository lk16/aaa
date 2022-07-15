from typing import List, Type

import pytest

from tests.aaa import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param('"foo" .', "foo", [], id="print"),
        pytest.param('"\\\\" .', "\\", [], id="print-backslash"),
        pytest.param('"\\n" .', "\n", [], id="print-newline"),
        pytest.param('"\\"" .', '"', [], id="print-quote"),
        pytest.param(
            '"\\x" .',
            "",
            [NotImplementedError],
            id="invalid-escape-sequence",
            marks=pytest.mark.skip,
        ),
        pytest.param("str .", "", [], id="print-zero-value"),
        pytest.param('"a" "b" + .', "ab", [], id="concatenate"),
        pytest.param('"" "a" + .', "a", [], id="concatenate-lhs-empty"),
        pytest.param('"a" "" + .', "a", [], id="concatenate-rhs-empty"),
        pytest.param('"" "" + .', "", [], id="concatenate-both-empty"),
        pytest.param('"aaa" "aaa" = .', "true", [], id="equals-true"),
        pytest.param('"aaa" "bbb" = .', "false", [], id="equals-false"),
    ],
)
def test_str(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_main(code, expected_output, expected_exception_types)
