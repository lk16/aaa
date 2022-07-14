from typing import List

from pytest import CaptureFixture

from aaa import main


def test_readme_command(capfd: CaptureFixture[str]) -> None:
    readme_commands: List[str] = []

    with open("README.md") as readme:
        for line in readme:
            if "aaa.py cmd" in line:
                readme_commands.append(line)

    command = '"a" 0 while dup 3 < { over . 1 + } drop drop "\\n" .'

    # README hasn't changed command and no commands were added
    assert command in readme_commands[0]
    assert len(readme_commands) == 1

    main(["./aaa.py", "cmd", command])

    stdout, _ = capfd.readouterr()
    assert str(stdout) == "aaa\n"
