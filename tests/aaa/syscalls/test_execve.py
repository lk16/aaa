from typing import Dict, List
from unittest.mock import patch

from tests.aaa import check_aaa_main


def test_execve() -> None:
    def mock_execve(path: str, argv: List[str], environ: Dict[str, str]) -> None:
        pass

    with patch("aaa.simulator.simulator.os.execve", mock_execve):
        check_aaa_main(
            '"/bin/foo" vec[str] "/bin/foo" vec:push map[str, str] execve', "", []
        )
