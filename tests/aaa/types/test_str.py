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
        pytest.param('"a b c" " " str:split .', '["a", "b", "c"]', [], id="split"),
        pytest.param('" a " str:strip .', "a", [], id="strip"),
        pytest.param('"abcd" 1 3 str:substr . .', "truebc", [], id="substr-ok"),
        pytest.param(
            '"abcd" 1 2 - 3 str:substr . .', "false", [], id="substr-fail-start"
        ),
        pytest.param('"abcd" 1 5 str:substr . . ', "false", [], id="substr-fail-end"),
        pytest.param(
            '"abcd" 1 2 - 5 str:substr . .', "false", [], id="substr-fail-both"
        ),
        pytest.param(
            '"abcd" 2 1 str:substr . .', "false", [], id="substr-start-after-end"
        ),
        pytest.param('"abcd" str:len .', "4", [], id="len"),
        pytest.param('"abcd" str:upper .', "ABCD", [], id="upper"),
        pytest.param('"ABCD" str:lower .', "abcd", [], id="lower"),
        pytest.param('"abcd" "bc" str:find . .', "true1", [], id="find-ok"),
        pytest.param('"abcd" "x" str:find . .', "false0", [], id="find-fail"),
        pytest.param(
            '"abcd" "bc" 1 str:find_after . .', "true1", [], id="find-after-ok"
        ),
        pytest.param(
            '"abcd" "bc" 2 str:find_after . .', "false0", [], id="find-after-fail"
        ),
        pytest.param('"123" str:to_int . .', "true123", [], id="to_int-ok"),
        pytest.param('"1x23" str:to_int . .', "false0", [], id="to_int-fail"),
        pytest.param(
            '"." vec[str] dup "a" vec:push dup "b" vec:push str:join .',
            "a.b",
            [],
            id="join",
        ),
        pytest.param('"a" "a" str:equals .', "true", [], id="equals-ok"),
        pytest.param('"a" "b" str:equals .', "false", [], id="equals-fail"),
        pytest.param('"abc" "b" str:contains .', "true", [], id="contains-ok"),
        pytest.param('"abc" "d" str:contains .', "false", [], id="contains-fail"),
        pytest.param('"true" str:to_bool . .', "truetrue", [], id="to_str-true"),
        pytest.param('"false" str:to_bool . .', "truefalse", [], id="to_str-false"),
        pytest.param('"foo" str:to_bool . .', "falsefalse", [], id="to_str-fail"),
        pytest.param('"abcd" "bc" "ef" str:replace .', "aefd", [], id="replace"),
        pytest.param('"abcd" "ef" str:append .', "abcdef", [], id="replace"),
    ],
)
def test_str(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_main(code, expected_output, expected_exception_types)
