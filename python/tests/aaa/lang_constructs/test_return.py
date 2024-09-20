import pytest

from tests.aaa import check_aaa_full_source


@pytest.mark.parametrize(
    ["code"],
    [
        pytest.param(
            """
            fn main { nop }
            fn foo return int {
                if true {
                    5 return
                }
                7
            }
            """,
            id="if-else",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo return int { 3 return }
            """,
            id="never-coerce",
        ),
    ],
)
def test_return(
    code: str,
) -> None:
    check_aaa_full_source(code, "", [])
