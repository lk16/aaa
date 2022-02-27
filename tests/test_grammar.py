from parser.grammar_generator import check_grammar_file_staleness

from aaa import GRAMMAR_FILE_PATH
from lang.parse import REWRITE_RULES, ROOT_SYMBOL


def test_grammar_up_to_date() -> None:
    stale, _ = check_grammar_file_staleness(
        GRAMMAR_FILE_PATH, REWRITE_RULES, ROOT_SYMBOL
    )

    assert (
        not stale
    ), 'Grammar is out of date, please run "./aaa.py generate-grammar-file".'
