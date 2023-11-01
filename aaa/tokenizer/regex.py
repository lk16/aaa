import re

REGULAR_CHARACTER = "([^'\t\n\r\f\v\\\\\"])"
SIMPLE_ESCAPED_CHARACTER = "(\\\\[/0befnrt\\\\\"'])"
SHORT_ESCAPED_UNICODE_CHARACTER = "(\\\\u[0-9a-fA-F]{4})"
LONG_ESCAPED_UNICODE_CHARACTER = "(\\\\U[0-9a-fA-F]{8})"

CHARACTER_REGEX = (
    "("
    + "|".join(
        [
            REGULAR_CHARACTER,
            SIMPLE_ESCAPED_CHARACTER,
            SHORT_ESCAPED_UNICODE_CHARACTER,
            LONG_ESCAPED_UNICODE_CHARACTER,
        ]
    )
    + ")"
)

CHARACTER_LITERAL_REGEX = "'(" + CHARACTER_REGEX + "|\")'"
STRING_LITERAL_REGEX = '"(' + CHARACTER_REGEX + "|')*\""

character_literal_regex = re.compile(CHARACTER_LITERAL_REGEX)
string_literal_regex = re.compile(STRING_LITERAL_REGEX)
