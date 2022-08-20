from lark.lark import Lark

# TODO instanciate all this in aaa/parser/parser.py

AAA_GRAMMAR_PATH = "lang/parse/aaa.lark"

aaa_builtins_parser = Lark(open(AAA_GRAMMAR_PATH).read(), start="builtins_file_root")
aaa_source_parser = Lark(open(AAA_GRAMMAR_PATH).read(), start="regular_file_root")
aaa_keyword_parser = Lark(open(AAA_GRAMMAR_PATH).read(), start="keyword")
