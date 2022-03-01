from lang.grammar import OPERATOR_KEYWORDS
from lang.instructions import OPERATOR_INSTRUCTIONS


def test_all_operators_have_instructions() -> None:
    operators = set(OPERATOR_KEYWORDS)
    operators_with_instruction = set(OPERATOR_INSTRUCTIONS.keys())

    assert operators == operators_with_instruction
