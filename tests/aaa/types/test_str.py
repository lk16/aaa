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
        pytest.param('"a b c" " " str:split . drop', '["a", "b", "c"]', [], id="split"),
        pytest.param('" a " str:strip .', "a", [], id="strip"),
        pytest.param('"abcd" 1 3 str:substr . . drop', "truebc", [], id="substr-ok"),
        pytest.param(
            '"abcd" 1 2 - 3 str:substr . . drop', "false", [], id="substr-fail-start"
        ),
        pytest.param(
            '"abcd" 1 5 str:substr . . drop', "false", [], id="substr-fail-end"
        ),
        pytest.param(
            '"abcd" 1 2 - 5 str:substr . . drop', "false", [], id="substr-fail-both"
        ),
        pytest.param(
            '"abcd" 2 1 str:substr . . drop', "false", [], id="substr-start-after-end"
        ),
        pytest.param('"abcd" str:len . drop', "4", [], id="len"),
        pytest.param('"abcd" str:upper . drop', "ABCD", [], id="upper"),
        pytest.param('"ABCD" str:lower . drop', "abcd", [], id="lower"),
        pytest.param('"abcd" "bc" str:find . . drop', "true1", [], id="find-ok"),
        pytest.param('"abcd" "x" str:find . . drop', "false0", [], id="find-fail"),
        pytest.param(
            '"abcd" "bc" 1 str:find_after . . drop', "true1", [], id="find-after-ok"
        ),
        pytest.param(
            '"abcd" "bc" 2 str:find_after . . drop', "false0", [], id="find-after-fail"
        ),
        pytest.param('"123" str:to_int . . drop', "true123", [], id="to_int-ok"),
        pytest.param('"1x23" str:to_int . . drop', "false0", [], id="to_int-fail"),
    ],
)
def test_str(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_main(code, expected_output, expected_exception_types)
