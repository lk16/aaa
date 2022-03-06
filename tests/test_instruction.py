from lang.grammar.keywords import get_operator_keywords
from lang.instructions import OPERATOR_INSTRUCTIONS


def test_all_operators_have_instructions() -> None:
    operator_keywords = get_operator_keywords()
    operators_with_instruction = set(OPERATOR_INSTRUCTIONS.keys())

    assert operator_keywords == operators_with_instruction
