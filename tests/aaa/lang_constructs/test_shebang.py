from tests.aaa import check_aaa_full_source


def test_shebang() -> None:
    code = "#!/usr/bin/env aaa\nfn main { 1 . }"
    expected_output = "1"
    check_aaa_full_source(code, expected_output, [])
