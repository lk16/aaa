from parser.grammar.parser import REWRITE_RULES
from parser.parser import parse_generic
from parser.parser_generator import check_parser_staleness, generate_parser
from pathlib import Path


def test_parser_not_stale() -> None:
    grammar_path = Path("lang/grammar/grammar.txt")
    parser_path = Path("lang/grammar/parser.py")

    parser_code = generate_parser(grammar_path)
    assert not check_parser_staleness(parser_code, parser_path)
