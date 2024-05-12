use lazy_static::lazy_static;

use super::{token::Token, token_type::TokenType};
use std::collections::HashMap;

#[derive(Default)]
pub struct SourceFile {
    pub enums: Vec<Enum>,
    pub functions: Vec<Function>,
    pub imports: Vec<Import>,
    pub structs: Vec<Struct>,
}

#[derive(Default)]
pub struct Enum {
    pub name: Identifier,
    pub parameters: Vec<Identifier>,
    pub variants: Vec<EnumVariant>,
}

#[derive(Default)]
pub struct Argument {
    pub name: Identifier,
    pub type_: Type,
}

#[derive(Default)]
pub struct Assignment {
    pub variables: Vec<Identifier>,
    pub body: FunctionBody,
}

pub struct Boolean {
    pub value: bool,
}

impl Boolean {
    pub fn new(token: Token) -> Self {
        let value = match token.type_ {
            TokenType::True => true,
            TokenType::False => false,
            _ => unreachable!(),
        };

        Self { value }
    }
}

#[derive(Default)]
pub struct Branch {
    pub condition: FunctionBody,
    pub then_body: FunctionBody,
    pub else_body: Option<FunctionBody>,
}

#[derive(Default)]
pub struct CaseBlock {
    pub label: CaseLabel,
    pub body: FunctionBody,
}
#[derive(Default)]

pub struct CaseLabel {
    pub enum_name: Identifier,
    pub enum_variant: Identifier,
    pub variables: Vec<Identifier>,
}

#[derive(Default)]
pub struct DefaultBlock {
    pub body: FunctionBody,
}

#[derive(Default)]
pub struct EnumVariant {
    pub name: Identifier,
    pub data: Vec<Type>,
}

#[derive(Default)]
pub struct ForeachLoop {
    pub body: FunctionBody,
}

#[derive(Default)]
pub struct FreeFunctionCall {
    pub name: Identifier,
    pub parameters: Vec<Type>,
}

#[derive(Default)]
pub struct FreeFunctionName {
    pub name: Identifier,
    pub parameters: Vec<Identifier>,
}

pub enum FunctionBodyItem {
    Assignment(Assignment),
    Branch(Branch),
    Boolean(Boolean),
    Call(Call),
    Char(Char),
    Foreach(ForeachLoop),
    FunctionCall(FunctionCall),
    FunctionType(FunctionType),
    GetFunction(GetFunction),
    Integer(Integer),
    Match(MatchBlock),
    Return(Return),
    GetField(GetField),
    SetField(SetField),
    Use(UseBlock),
    While(WhileLoop),
    String(ParsedString),
}

#[derive(Default)]
pub struct FunctionBody {
    pub items: Vec<FunctionBodyItem>,
}

pub enum FunctionCall {
    Member(MemberFunctionCall),
    Free(FreeFunctionCall),
}

#[derive(Default)]
pub struct Function {
    pub name: FunctionName,
    pub arguments: Vec<Argument>,
    pub return_types: ReturnTypes,
    pub body: Option<FunctionBody>,
}

pub enum FunctionName {
    Member(MemberFunctionName),
    Free(FreeFunctionName),
}

impl Default for FunctionName {
    fn default() -> Self {
        return Self::Free(FreeFunctionName::default());
    }
}

pub struct GetFunction {
    pub target: ParsedString,
}

impl GetFunction {
    pub fn new(token: Token) -> Self {
        Self {
            target: ParsedString::new(token),
        }
    }
}

#[derive(Default)]
pub struct ImportItem {
    pub name: Identifier,
    pub alias: Option<Identifier>,
}

#[derive(Default)]
pub struct Import {
    pub source: ParsedString,
    pub items: Vec<ImportItem>,
}

#[derive(Default)]
pub struct MatchBlock {
    pub case_blocks: Vec<CaseBlock>,
    pub default_blocks: Vec<DefaultBlock>,
}

#[derive(Default)]

pub struct MemberFunctionCall {
    pub type_name: Identifier,
    pub func_name: Identifier,
    pub parameters: Vec<Type>,
}

#[derive(Default)]
pub struct MemberFunctionName {
    pub type_name: Identifier,
    pub func_name: Identifier,
    pub parameters: Vec<Identifier>,
}

pub enum ReturnTypes {
    Never,
    Sometimes(Vec<Type>),
}

impl Default for ReturnTypes {
    fn default() -> Self {
        return ReturnTypes::Sometimes(vec![]);
    }
}

#[derive(Default)]
pub struct Struct {
    pub name: Identifier,
    pub parameters: Vec<Identifier>,
    pub fields: Option<Vec<StructField>>,
}

pub struct GetField {
    pub field_name: ParsedString,
}

impl GetField {
    pub fn new(token: Token) -> Self {
        Self {
            field_name: ParsedString::new(token),
        }
    }
}

pub struct SetField {
    pub field_name: ParsedString,
    pub body: FunctionBody,
}

impl SetField {
    pub fn new(token: Token, body: FunctionBody) -> Self {
        Self {
            field_name: ParsedString::new(token),
            body,
        }
    }
}

#[derive(Default)]
pub struct StructField {
    pub name: Identifier,
    pub type_: Type,
}

#[derive(Default)]
pub struct RegularType {
    pub is_const: bool,
    pub name: Identifier,
    pub parameters: Vec<Type>,
}

#[derive(Default)]
pub struct FunctionType {
    pub argument_types: Vec<Type>,
    pub return_types: ReturnTypes,
}

pub enum Type {
    Regular(RegularType),
    Function(FunctionType),
}

impl Default for Type {
    fn default() -> Self {
        return Self::Regular(RegularType::default());
    }
}

#[derive(Default)]
pub struct UseBlock {
    pub variables: Vec<Identifier>,
    pub body: FunctionBody,
}

#[derive(Default)]
pub struct WhileLoop {
    pub condition: FunctionBody,
    pub body: FunctionBody,
}

#[derive(Default)]
pub struct Identifier {
    pub value: String,
}

pub struct Call {}

pub struct Char {
    pub value: char,
}

impl Char {
    pub fn new(token: Token) -> Self {
        let string = ParsedString::new(token);
        Self {
            value: string.value.chars().next().unwrap(),
        }
    }
}

pub struct Integer {
    pub value: isize,
}

impl Integer {
    pub fn new(token: Token) -> Self {
        Self {
            value: token.value.parse().unwrap(),
        }
    }
}

pub struct Return {}

#[derive(Default)]
pub struct ParsedString {
    pub value: String,
}

impl ParsedString {
    pub fn new(token: Token) -> Self {
        Self {
            value: unescape_string(&token.value[1..token.len() - 1]),
        }
    }
}

lazy_static! {
    static ref ESCAPE_SEQUENCES: HashMap<char, char> = {
        let mut escape_sequences = HashMap::new();
        escape_sequences.insert('"', '"');
        escape_sequences.insert('\'', '\'');
        escape_sequences.insert('/', '/');
        escape_sequences.insert('\\', '\\');
        escape_sequences.insert('0', '\0');
        escape_sequences.insert('b', '\u{0008}'); // backspace
        escape_sequences.insert('e', '\u{001B}'); // escape
        escape_sequences.insert('f', '\u{000C}'); // form feed
        escape_sequences.insert('n', '\n');       // newline
        escape_sequences.insert('r', '\r');       // carriage return
        escape_sequences.insert('t', '\t');       // tab
        escape_sequences
    };
}

fn unescape_string(escaped: &str) -> String {
    let mut unescaped = String::new();
    let mut offset = 0;
    let escaped_chars: Vec<char> = escaped.chars().collect();

    while offset < escaped_chars.len() {
        if let Some(backslash_offset) = escaped_chars[offset..].iter().position(|&c| c == '\\') {
            let backslash_offset = offset + backslash_offset;
            unescaped.extend(&escaped_chars[offset..backslash_offset]);

            if backslash_offset + 1 >= escaped_chars.len() {
                break;
            }

            let escape_determinant = escaped_chars[backslash_offset + 1];

            if let Some(&unescaped_char) = ESCAPE_SEQUENCES.get(&escape_determinant) {
                unescaped.push(unescaped_char);
                offset = backslash_offset + 2;
                continue;
            }

            if escape_determinant == 'u' && backslash_offset + 6 <= escaped_chars.len() {
                let unicode_hex: String = escaped_chars[backslash_offset + 2..backslash_offset + 6]
                    .iter()
                    .collect();
                if let Ok(unicode_value) = u32::from_str_radix(&unicode_hex, 16) {
                    if let Some(unicode_char) = std::char::from_u32(unicode_value) {
                        unescaped.push(unicode_char);
                        offset = backslash_offset + 6;
                        continue;
                    }
                }
            }

            if escape_determinant == 'U' && backslash_offset + 10 <= escaped_chars.len() {
                let unicode_hex: String = escaped_chars
                    [backslash_offset + 2..backslash_offset + 10]
                    .iter()
                    .collect();
                if let Ok(unicode_value) = u32::from_str_radix(&unicode_hex, 16) {
                    if let Some(unicode_char) = std::char::from_u32(unicode_value) {
                        unescaped.push(unicode_char);
                        offset = backslash_offset + 10;
                        continue;
                    }
                }
            }

            // Unknown escape sequence
            unreachable!();
        } else {
            unescaped.extend(&escaped_chars[offset..]);
            break;
        }
    }

    unescaped
}

#[cfg(test)]
mod tests {
    use super::unescape_string;
    use rstest::rstest;

    #[rstest]
    #[case("", "")]
    #[case("", "")]
    #[case("abc", "abc")]
    #[case("\\\\", "\\")]
    #[case("a\\\\b", "a\\b")]
    #[case("\\\\b", "\\b")]
    #[case("a\\\\", "a\\")]
    #[case("a\\\"b", "a\"b")]
    #[case("a\\'b", "a'b")]
    #[case("a\\/b", "a/b")]
    #[case("a\\0b", "a\0b")]
    #[case("a\\bb", "a\u{0008}b")]
    #[case("a\\eb", "a\u{001b}b")]
    #[case("a\\fb", "a\u{000c}b")]
    #[case("a\\nb", "a\nb")]
    #[case("a\\rb", "a\rb")]
    #[case("a\\tb", "a\tb")]
    #[case("a\\u0000b", "a\u{0000}b")]
    #[case("a\\u9999b", "a\u{9999}b")]
    #[case("a\\uaaaab", "a\u{aaaa}b")]
    #[case("a\\uffffb", "a\u{ffff}b")]
    #[case("a\\uAAAAb", "a\u{aaaa}b")]
    #[case("a\\uFFFFb", "a\u{ffff}b")]
    #[case("a\\U00000000b", "a\u{000000}b")]
    #[case("a\\U0001F600b", "a\u{01F600}b")]
    fn test_unescape_string(#[case] escaped: &str, #[case] expected_unescaped: &str) {
        let unescaped = unescape_string(escaped);
        assert_eq!(unescaped, expected_unescaped);
    }
}
