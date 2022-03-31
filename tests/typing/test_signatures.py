from lang.instructions.generator import OPERATOR_INSTRUCTIONS
from lang.typing.signatures import OPERATOR_SIGNATURES


def test_all_signatures_present() -> None:
    assert OPERATOR_INSTRUCTIONS.keys() == OPERATOR_SIGNATURES.keys()
