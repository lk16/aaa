from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import List

from pytest import CaptureFixture

from aaa.run import Runner


def test_readme_command(capfd: CaptureFixture[str]) -> None:
    readme_commands: List[str] = []

    with open("README.md") as readme:
        for line in readme:
            if 'manage.py cmd \'fn main { "a"' in line:
                readme_commands.append(line)

    command = '"a" 0 while dup 3 < { over . 1 + } drop drop "\\n" .'

    # README hasn't changed command and no commands were added
    assert command in readme_commands[0]
    assert len(readme_commands) == 1

    with NamedTemporaryFile(delete=False) as temp_file:
        file = Path(gettempdir()) / temp_file.name
        file.write_text("fn main { " + command + " }")
        Runner(file, None, False).run()

    stdout, stderr = capfd.readouterr()
    assert str(stderr) == ""
    assert str(stdout) == "aaa\n"
