from pathlib import Path

from lark.lark import Lark

AAA_GRAMMAR_PATH = Path(__file__).parent / "aaa.lark"

aaa_builtins_parser = Lark(open(AAA_GRAMMAR_PATH).read(), start="builtins_file_root")
aaa_source_parser = Lark(open(AAA_GRAMMAR_PATH).read(), start="regular_file_root")
aaa_keyword_parser = Lark(open(AAA_GRAMMAR_PATH).read(), start="keyword")
