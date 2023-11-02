import re

REGULAR_CHARACTER = "([^'\t\n\r\f\v\\\\\"])"
ESCACPED_CHAR_SIMPLE = "(\\\\[/0befnrt\\\\\"'])"
ESCAPED_CHAR_TWO_HEX = "(\\\\x[0-9a-fA-F]{2})"  # TODO #190 add tests for this
ESCAPED_CHAR_FOUR_HEX = "(\\\\u[0-9a-fA-F]{4})"
ESCAPED_CHAR_SIX_HEX = "(\\\\U((0[0-9])|10)[0-9a-fA-F]{4})"

CHARACTER_REGEX = (
    "("
    + "|".join(
        [
            REGULAR_CHARACTER,
            ESCACPED_CHAR_SIMPLE,
            ESCAPED_CHAR_TWO_HEX,
            ESCAPED_CHAR_FOUR_HEX,
            ESCAPED_CHAR_SIX_HEX,
        ]
    )
    + ")"
)

CHARACTER_LITERAL_REGEX = "'(" + CHARACTER_REGEX + "|\")'"
STRING_LITERAL_REGEX = '"(' + CHARACTER_REGEX + "|')*\""

character_literal_regex = re.compile(CHARACTER_LITERAL_REGEX)
string_literal_regex = re.compile(STRING_LITERAL_REGEX)
whitespace_regex = re.compile("\\s+")
comment_regex = re.compile("//[^\n]*")
integer_regex = re.compile("(-)?[0-9]+")
identifier_regex = re.compile("[a-zA-Z_]+")
