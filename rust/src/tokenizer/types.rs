use lazy_static::lazy_static;
use regex::Regex;

use crate::common::{position::Position, traits::HasPosition};

#[derive(Debug, Default, Clone)]
pub struct Token {
    pub type_: TokenType,
    pub value: String,
    position: Position,
}

impl Token {
    pub fn new(type_: TokenType, value: String, position: Position) -> Self {
        Token {
            type_,
            value,
            position,
        }
    }

    pub fn len(&self) -> usize {
        self.value.len()
    }

    pub fn end(&self) -> Position {
        self.position.after(&self.value)
    }
}

impl HasPosition for Token {
    fn position(&self) -> Position {
        return self.position.clone();
    }
}

#[derive(Copy, Clone, Debug, PartialEq, Default)]
pub enum TokenType {
    // Keyword tokens
    #[default]
    Args,
    As,
    Builtin,
    Call,
    Case,
    Const,
    Default,
    Else,
    Enum,
    False,
    Foreach,
    From,
    Fn,
    If,
    Import,
    Match,
    Never,
    Return,
    Struct,
    True,
    Use,
    While,

    // Other tokens
    Assign,
    Char,
    Colon,
    Comma,
    Comment,
    End,
    GetField,
    Identifier,
    Integer,
    Operator,
    SetField,
    SqEnd,
    SqStart,
    Start,
    String,
    Whitespace,
}

impl TokenType {
    #[cfg(test)]
    fn is_keyword(&self) -> bool {
        match self {
            TokenType::Args
            | TokenType::As
            | TokenType::Builtin
            | TokenType::Call
            | TokenType::Case
            | TokenType::Const
            | TokenType::Default
            | TokenType::Else
            | TokenType::Enum
            | TokenType::False
            | TokenType::Foreach
            | TokenType::From
            | TokenType::Fn
            | TokenType::If
            | TokenType::Import
            | TokenType::Match
            | TokenType::Never
            | TokenType::Return
            | TokenType::Struct
            | TokenType::True
            | TokenType::Use
            | TokenType::While => true,
            _ => false,
        }
    }

    pub fn is_filtered(&self) -> bool {
        match self {
            TokenType::Comment | TokenType::Whitespace => true,
            _ => false,
        }
    }
}

const TOKEN_TYPE_REGEXES: &[(TokenType, &'static str, usize)] = &[
    (TokenType::Args, "(args)([^_a-zA-Z]|$)", 1),
    (TokenType::As, "(as)([^_a-zA-Z]|$)", 1),
    (TokenType::Builtin, "(builtin)([^_a-zA-Z]|$)", 1),
    (TokenType::Call, "(call)([^_a-zA-Z]|$)", 1),
    (TokenType::Case, "(case)([^_a-zA-Z]|$)", 1),
    (TokenType::Const, "(const)([^_a-zA-Z]|$)", 1),
    (TokenType::Default, "(default)([^_a-zA-Z]|$)", 1),
    (TokenType::Else, "(else)([^_a-zA-Z]|$)", 1),
    (TokenType::Enum, "(enum)([^_a-zA-Z]|$)", 1),
    (TokenType::False, "(false)([^_a-zA-Z]|$)", 1),
    (TokenType::Foreach, "(foreach)([^_a-zA-Z]|$)", 1),
    (TokenType::From, "(from)([^_a-zA-Z]|$)", 1),
    (TokenType::Fn, "(fn)([^_a-zA-Z]|$)", 1),
    (TokenType::If, "(if)([^_a-zA-Z]|$)", 1),
    (TokenType::Import, "(import)([^_a-zA-Z]|$)", 1),
    (TokenType::Match, "(match)([^_a-zA-Z]|$)", 1),
    (TokenType::Never, "(never)([^_a-zA-Z]|$)", 1),
    (TokenType::Return, "(return)([^_a-zA-Z]|$)", 1),
    (TokenType::Struct, "(struct)([^_a-zA-Z]|$)", 1),
    (TokenType::True, "(true)([^_a-zA-Z]|$)", 1),
    (TokenType::Use, "(use)([^_a-zA-Z]|$)", 1),
    (TokenType::While, "(while)([^_a-zA-Z]|$)", 1),
    (TokenType::Assign, "<-", 0),
    (TokenType::End, "}", 0),
    (TokenType::Start, "\\{", 0),
    (TokenType::Char, "'([^'\\t\\n\\r\\f\\v\\\\])'", 0),
    (TokenType::Char, "'(\\\\[/0befnrt\\\\\"'])'", 0),
    (TokenType::Char, "'(\\\\x[0-9a-fA-F]{2})'", 0),
    (TokenType::Char, "'(\\\\u[0-9a-fA-F]{4})'", 0),
    (TokenType::Char, "'(\\\\U((0[0-9])|10)[0-9a-fA-F]{4})'", 0),
    (TokenType::Colon, ":", 0),
    (TokenType::Comma, ",", 0),
    (TokenType::Comment, "//[^\n]*", 0),
    (TokenType::GetField, "\\?", 0),
    (TokenType::Identifier, "[a-zA-Z_]+", 0),
    (TokenType::Integer, "(-)?[0-9]+", 0),
    (TokenType::Operator, "!=", 0),
    (TokenType::Operator, "(-)([^0-9]|$)", 1),
    (TokenType::Operator, "(/)([^/]|$)", 1),
    (TokenType::Operator, "\\.", 0),
    (TokenType::Operator, "\\*", 0),
    (TokenType::Operator, "\\+", 0),
    (TokenType::Operator, "%", 0),
    (TokenType::Operator, "<=", 0),
    (TokenType::Operator, "<", 0),
    (TokenType::Operator, "=", 0),
    (TokenType::Operator, ">=", 0),
    (TokenType::Operator, ">", 0),
    (TokenType::SetField, "!", 0),
    (TokenType::SqEnd, "]", 0),
    (TokenType::SqStart, "\\[", 0),
    (TokenType::String, "\"(([^'\\t\\n\\r\\f\\v\\\\\"])|(\\\\[/0befnrt\\\\\"'])|(\\\\x[0-9a-fA-F]{2})|(\\\\u[0-9a-fA-F]{4})|(\\\\U((0[0-9])|10)[0-9a-fA-F]{4})|')*\"", 0),
    (TokenType::Whitespace, "\\s+", 0),
];

lazy_static! {
    pub static ref ENUM_REGEX_PAIRS: Vec<(TokenType, Regex, usize)> = {
        let mut pairs = Vec::new();
        for (token_type, pattern, group) in TOKEN_TYPE_REGEXES.iter() {
            let regex = Regex::new(pattern).expect("Failed to compile regex pattern");
            pairs.push((*token_type, regex, *group));
        }
        pairs
    };
}

#[cfg(test)]
mod tests {
    use std::fs;

    use super::super::super::common::files::find_aaa_files;
    use super::super::tokenizer::tokenize;
    use super::{TokenType, TOKEN_TYPE_REGEXES};
    use rstest::rstest;

    #[test]
    fn test_token_type_regex_order() {
        let last_keyword_token_offset = TOKEN_TYPE_REGEXES
            .iter()
            .enumerate()
            .filter(|(_, (token_type, _, _))| token_type.is_keyword())
            .map(|(index, _)| index)
            .max()
            .unwrap();

        let first_non_keyword_token_offset = TOKEN_TYPE_REGEXES
            .iter()
            .enumerate()
            .filter(|(_, (token_type, _, _))| !token_type.is_keyword())
            .map(|(index, _)| index)
            .min()
            .unwrap();

        assert!(last_keyword_token_offset < first_non_keyword_token_offset);
    }

    #[rstest]
    #[case("args", Some(TokenType::Args))]
    #[case("args_", Some(TokenType::Identifier))]
    #[case("argsx", Some(TokenType::Identifier))]
    #[case("as", Some(TokenType::As))]
    #[case("as_", Some(TokenType::Identifier))]
    #[case("asx", Some(TokenType::Identifier))]
    #[case("builtin", Some(TokenType::Builtin))]
    #[case("builtin_", Some(TokenType::Identifier))]
    #[case("builtinx", Some(TokenType::Identifier))]
    #[case("call", Some(TokenType::Call))]
    #[case("call_", Some(TokenType::Identifier))]
    #[case("callx", Some(TokenType::Identifier))]
    #[case("case", Some(TokenType::Case))]
    #[case("case_", Some(TokenType::Identifier))]
    #[case("casex", Some(TokenType::Identifier))]
    #[case("const", Some(TokenType::Const))]
    #[case("const_", Some(TokenType::Identifier))]
    #[case("constx", Some(TokenType::Identifier))]
    #[case("default", Some(TokenType::Default))]
    #[case("default_", Some(TokenType::Identifier))]
    #[case("defaultx", Some(TokenType::Identifier))]
    #[case("else", Some(TokenType::Else))]
    #[case("else_", Some(TokenType::Identifier))]
    #[case("elsex", Some(TokenType::Identifier))]
    #[case("enum", Some(TokenType::Enum))]
    #[case("enum_", Some(TokenType::Identifier))]
    #[case("enumx", Some(TokenType::Identifier))]
    #[case("false", Some(TokenType::False))]
    #[case("false_", Some(TokenType::Identifier))]
    #[case("falsex", Some(TokenType::Identifier))]
    #[case("foreach", Some(TokenType::Foreach))]
    #[case("foreach_", Some(TokenType::Identifier))]
    #[case("foreachx", Some(TokenType::Identifier))]
    #[case("from", Some(TokenType::From))]
    #[case("from_", Some(TokenType::Identifier))]
    #[case("fromx", Some(TokenType::Identifier))]
    #[case("fn", Some(TokenType::Fn))]
    #[case("fn_", Some(TokenType::Identifier))]
    #[case("fnx", Some(TokenType::Identifier))]
    #[case("if", Some(TokenType::If))]
    #[case("if_", Some(TokenType::Identifier))]
    #[case("ifx", Some(TokenType::Identifier))]
    #[case("import", Some(TokenType::Import))]
    #[case("import_", Some(TokenType::Identifier))]
    #[case("importx", Some(TokenType::Identifier))]
    #[case("match", Some(TokenType::Match))]
    #[case("match_", Some(TokenType::Identifier))]
    #[case("matchx", Some(TokenType::Identifier))]
    #[case("never", Some(TokenType::Never))]
    #[case("never_", Some(TokenType::Identifier))]
    #[case("neverx", Some(TokenType::Identifier))]
    #[case("return", Some(TokenType::Return))]
    #[case("return_", Some(TokenType::Identifier))]
    #[case("returnx", Some(TokenType::Identifier))]
    #[case("struct", Some(TokenType::Struct))]
    #[case("struct_", Some(TokenType::Identifier))]
    #[case("structx", Some(TokenType::Identifier))]
    #[case("true", Some(TokenType::True))]
    #[case("true_", Some(TokenType::Identifier))]
    #[case("truex", Some(TokenType::Identifier))]
    #[case("use", Some(TokenType::Use))]
    #[case("use_", Some(TokenType::Identifier))]
    #[case("usex", Some(TokenType::Identifier))]
    #[case("while", Some(TokenType::While))]
    #[case("while_", Some(TokenType::Identifier))]
    #[case("whilex", Some(TokenType::Identifier))]
    #[case("<-", Some(TokenType::Assign))]
    #[case("}", Some(TokenType::End))]
    #[case("{", Some(TokenType::Start))]
    #[case("'a'", Some(TokenType::Char))]
    #[case("'A'", Some(TokenType::Char))]
    #[case("'z'", Some(TokenType::Char))]
    #[case("'Z'", Some(TokenType::Char))]
    #[case("'a'", Some(TokenType::Char))]
    #[case("'''", None)]
    #[case("'\t'", None)]
    #[case("'\n'", None)]
    #[case("'\r'", None)]
    #[case("'\x0C'", None)] // \f form feed
    #[case("'\x0B'", None)] // \v vertical tab
    #[case("'\\'", None)]
    #[case("'\\/'", Some(TokenType::Char))]
    #[case("'\\0'", Some(TokenType::Char))]
    #[case("'\\b'", Some(TokenType::Char))]
    #[case("'\\e'", Some(TokenType::Char))]
    #[case("'\\f'", Some(TokenType::Char))]
    #[case("'\\n'", Some(TokenType::Char))]
    #[case("'\\r'", Some(TokenType::Char))]
    #[case("'\\t'", Some(TokenType::Char))]
    #[case("'\\\\'", Some(TokenType::Char))]
    #[case("'\\x00'", Some(TokenType::Char))]
    #[case("'\\x99'", Some(TokenType::Char))]
    #[case("'\\xaa'", Some(TokenType::Char))]
    #[case("'\\xff'", Some(TokenType::Char))]
    #[case("'\\xAA'", Some(TokenType::Char))]
    #[case("'\\xFF'", Some(TokenType::Char))]
    #[case("'\\x0'", None)]
    #[case("'\\x000'", None)]
    #[case("'\\u0000'", Some(TokenType::Char))]
    #[case("'\\u9999'", Some(TokenType::Char))]
    #[case("'\\uaaaa'", Some(TokenType::Char))]
    #[case("'\\uffff'", Some(TokenType::Char))]
    #[case("'\\uAAAA'", Some(TokenType::Char))]
    #[case("'\\uFFFF'", Some(TokenType::Char))]
    #[case("'\\u000'", None)]
    #[case("'\\u00000'", None)]
    #[case("'\\U000000'", Some(TokenType::Char))]
    #[case("'\\U009999'", Some(TokenType::Char))]
    #[case("'\\U00aaaa'", Some(TokenType::Char))]
    #[case("'\\U00ffff'", Some(TokenType::Char))]
    #[case("'\\U00AAAA'", Some(TokenType::Char))]
    #[case("'\\U00FFFF'", Some(TokenType::Char))]
    #[case("'\\U0A0000'", None)]
    #[case("'\\U0A9999'", None)]
    #[case("'\\U0Aaaaa'", None)]
    #[case("'\\U0Affff'", None)]
    #[case("'\\U0AAAAA'", None)]
    #[case("'\\U0AFFFF'", None)]
    #[case("'\\U000000'", Some(TokenType::Char))]
    #[case("'\\U099999'", Some(TokenType::Char))]
    #[case("'\\U09aaaa'", Some(TokenType::Char))]
    #[case("'\\U09ffff'", Some(TokenType::Char))]
    #[case("'\\U09AAAA'", Some(TokenType::Char))]
    #[case("'\\U09FFFF'", Some(TokenType::Char))]
    #[case("'\\U109999'", Some(TokenType::Char))]
    #[case("'\\U10aaaa'", Some(TokenType::Char))]
    #[case("'\\U10ffff'", Some(TokenType::Char))]
    #[case("'\\U10AAAA'", Some(TokenType::Char))]
    #[case("'\\U10FFFF'", Some(TokenType::Char))]
    #[case("'\\U119999'", None)]
    #[case("'\\U11aaaa'", None)]
    #[case("'\\U11ffff'", None)]
    #[case("'\\U11AAAA'", None)]
    #[case("'\\U11FFFF'", None)]
    #[case("'\\U00000'", None)]
    #[case("'\\U0000000'", None)]
    #[case(":", Some(TokenType::Colon))]
    #[case(",", Some(TokenType::Comma))]
    #[case("//", Some(TokenType::Comment))]
    #[case("// foo", Some(TokenType::Comment))]
    #[case("?", Some(TokenType::GetField))]
    #[case("a", Some(TokenType::Identifier))]
    #[case("z", Some(TokenType::Identifier))]
    #[case("A", Some(TokenType::Identifier))]
    #[case("Z", Some(TokenType::Identifier))]
    #[case("_", Some(TokenType::Identifier))]
    #[case("aaaa", Some(TokenType::Identifier))]
    #[case("zzzz", Some(TokenType::Identifier))]
    #[case("AAAA", Some(TokenType::Identifier))]
    #[case("ZZZZ", Some(TokenType::Identifier))]
    #[case("____", Some(TokenType::Identifier))]
    #[case("0", Some(TokenType::Integer))]
    #[case("9", Some(TokenType::Integer))]
    #[case("0000", Some(TokenType::Integer))]
    #[case("9999", Some(TokenType::Integer))]
    #[case("-0000", Some(TokenType::Integer))]
    #[case("-9999", Some(TokenType::Integer))]
    #[case("!=", Some(TokenType::Operator))]
    #[case("-", Some(TokenType::Operator))]
    #[case("/", Some(TokenType::Operator))]
    #[case(".", Some(TokenType::Operator))]
    #[case("*", Some(TokenType::Operator))]
    #[case("+", Some(TokenType::Operator))]
    #[case("%", Some(TokenType::Operator))]
    #[case("<", Some(TokenType::Operator))]
    #[case("<=", Some(TokenType::Operator))]
    #[case("=", Some(TokenType::Operator))]
    #[case(">", Some(TokenType::Operator))]
    #[case(">=", Some(TokenType::Operator))]
    #[case("!", Some(TokenType::SetField))]
    #[case("[", Some(TokenType::SqStart))]
    #[case("]", Some(TokenType::SqEnd))]
    #[case("\"a\"", Some(TokenType::String))]
    #[case("\"A\"", Some(TokenType::String))]
    #[case("\"z\"", Some(TokenType::String))]
    #[case("\"Z\"", Some(TokenType::String))]
    #[case("\"a\"", Some(TokenType::String))]
    #[case("\"\"\"", None)]
    #[case("\"\t\"", None)]
    #[case("\"\n\"", None)]
    #[case("\"\r\"", None)]
    #[case("\"\x0C\"", None)] // \f form feed
    #[case("\"\x0B\"", None)] // \v vertical tab
    #[case("\"\\\"", None)]
    #[case("\"\\/\"", Some(TokenType::String))]
    #[case("\"\\0\"", Some(TokenType::String))]
    #[case("\"\\b\"", Some(TokenType::String))]
    #[case("\"\\e\"", Some(TokenType::String))]
    #[case("\"\\f\"", Some(TokenType::String))]
    #[case("\"\\n\"", Some(TokenType::String))]
    #[case("\"\\r\"", Some(TokenType::String))]
    #[case("\"\\t\"", Some(TokenType::String))]
    #[case("\"\\\\\"", Some(TokenType::String))]
    #[case("\"\\x00\"", Some(TokenType::String))]
    #[case("\"\\x99\"", Some(TokenType::String))]
    #[case("\"\\xaa\"", Some(TokenType::String))]
    #[case("\"\\xff\"", Some(TokenType::String))]
    #[case("\"\\xAA\"", Some(TokenType::String))]
    #[case("\"\\xFF\"", Some(TokenType::String))]
    #[case("\"\\x0\"", None)]
    #[case("\"\\x000\"", Some(TokenType::String))]
    #[case("\"\\u0000\"", Some(TokenType::String))]
    #[case("\"\\u9999\"", Some(TokenType::String))]
    #[case("\"\\uaaaa\"", Some(TokenType::String))]
    #[case("\"\\uffff\"", Some(TokenType::String))]
    #[case("\"\\uAAAA\"", Some(TokenType::String))]
    #[case("\"\\uFFFF\"", Some(TokenType::String))]
    #[case("\"\\u000\"", None)]
    #[case("\"\\u00000\"", Some(TokenType::String))]
    #[case("\"\\U000000\"", Some(TokenType::String))]
    #[case("\"\\U009999\"", Some(TokenType::String))]
    #[case("\"\\U00aaaa\"", Some(TokenType::String))]
    #[case("\"\\U00ffff\"", Some(TokenType::String))]
    #[case("\"\\U00AAAA\"", Some(TokenType::String))]
    #[case("\"\\U00FFFF\"", Some(TokenType::String))]
    #[case("\"\\U0A0000\"", None)]
    #[case("\"\\U0A9999\"", None)]
    #[case("\"\\U0Aaaaa\"", None)]
    #[case("\"\\U0Affff\"", None)]
    #[case("\"\\U0AAAAA\"", None)]
    #[case("\"\\U0AFFFF\"", None)]
    #[case("\"\\U000000\"", Some(TokenType::String))]
    #[case("\"\\U099999\"", Some(TokenType::String))]
    #[case("\"\\U09aaaa\"", Some(TokenType::String))]
    #[case("\"\\U09ffff\"", Some(TokenType::String))]
    #[case("\"\\U09AAAA\"", Some(TokenType::String))]
    #[case("\"\\U09FFFF\"", Some(TokenType::String))]
    #[case("\"\\U109999\"", Some(TokenType::String))]
    #[case("\"\\U10aaaa\"", Some(TokenType::String))]
    #[case("\"\\U10ffff\"", Some(TokenType::String))]
    #[case("\"\\U10AAAA\"", Some(TokenType::String))]
    #[case("\"\\U10FFFF\"", Some(TokenType::String))]
    #[case("\"\\U119999\"", None)]
    #[case("\"\\U11aaaa\"", None)]
    #[case("\"\\U11ffff\"", None)]
    #[case("\"\\U11AAAA\"", None)]
    #[case("\"\\U11FFFF\"", None)]
    #[case("\"\\U00000\"", None)]
    #[case("\"\\U0000000\"", Some(TokenType::String))]
    #[case("\"'\"", Some(TokenType::String))]
    #[case(" ", Some(TokenType::Whitespace))]
    #[case("  ", Some(TokenType::Whitespace))]
    #[case("\n", Some(TokenType::Whitespace))]
    fn test_tokenizer(#[case] code: &str, #[case] expected_token: Option<TokenType>) {
        let token = match tokenize(code, None) {
            Ok(tokens) => {
                assert_eq!(tokens.len(), 1);
                Some(tokens[0].type_)
            }
            Err(_) => None,
        };
        assert_eq!(expected_token, token);
    }

    #[test]
    fn test_tokenize_all_files() {
        for path in find_aaa_files().iter() {
            let code = fs::read_to_string(path).unwrap();
            tokenize(&code, Some(path.clone())).unwrap();
        }
    }
}
