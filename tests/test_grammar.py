from parser.grammar_generator import check_grammar_file_staleness
from pathlib import Path

from lang.parse import REWRITE_RULES, ROOT_SYMBOL


def test_grammar_up_to_date() -> None:
    grammar_file = Path("grammar.txt")
    stale, _ = check_grammar_file_staleness(grammar_file, REWRITE_RULES, ROOT_SYMBOL)

    assert (
        not stale
    ), 'Grammar is out of date, please run "./aaa.py generate-grammar-file".'
