from parser.parser_generator.parser_generator import ParserGenerator
from pathlib import Path


def test_parser_not_stale() -> None:
    grammar_path = Path("lang/grammar/grammar.txt")
    parser_path = Path("lang/grammar/parser.py")

    assert ParserGenerator(grammar_path).is_up_to_date(parser_path)
