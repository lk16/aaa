import pytest

from tests.aaa import check_aaa_main


@pytest.mark.parametrize(
    ["exit_code"], [pytest.param(i, id=f"exit-{i}") for i in range(3)]
)
def test_exit(exit_code: int) -> None:
    with pytest.raises(SystemExit) as e:
        check_aaa_main(f"{exit_code} exit", "", [])
    assert e.value.code == exit_code
