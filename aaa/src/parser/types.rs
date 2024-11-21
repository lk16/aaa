use lazy_static::lazy_static;

use std::{
    collections::HashMap,
    fmt::Display,
    path::{Path, PathBuf, MAIN_SEPARATOR_STR},
};

use crate::{
    common::{files::normalize_path, position::Position, traits::HasPosition},
    tokenizer::types::{Token, TokenType},
};

#[derive(Default)]
pub struct SourceFile {
    pub enums: Vec<Enum>,
    pub functions: Vec<Function>,
    pub imports: Vec<Import>,
    pub structs: Vec<Struct>,
    pub interfaces: Vec<Interface>,
}

impl SourceFile {
    pub fn dependencies(&self, current_dir: &Path) -> Vec<PathBuf> {
        self.imports
            .iter()
            .map(|import| import.get_source_path(current_dir))
            .collect()
    }
}

#[derive(Clone, Default)]
pub struct Enum {
    pub position: Position,
    pub name: Identifier,
    pub parameters: Vec<Identifier>,
    pub variants: Vec<EnumVariant>,
    pub is_builtin: bool,
}

#[derive(Clone, Default)]
pub struct Argument {
    pub position: Position,
    pub name: Identifier,
    pub type_: Type,
}

impl HasPosition for Argument {
    fn position(&self) -> Position {
        self.position.clone()
    }
}

impl Display for Argument {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "argument {}", self.name.value)
    }
}

#[derive(Clone, Default)]
pub struct Assignment {
    pub position: Position,
    pub variables: Vec<Identifier>,
    pub body: FunctionBody,
}

#[derive(Clone)]
pub struct Boolean {
    pub position: Position,
    pub value: bool,
}

impl Boolean {
    pub fn new(token: &Token) -> Self {
        let value = match token.type_ {
            TokenType::True => true,
            TokenType::False => false,
            _ => unreachable!(),
        };

        Self {
            position: token.position().clone(),
            value,
        }
    }
}

#[derive(Clone, Default)]
pub struct Branch {
    pub position: Position,
    pub condition: FunctionBody,
    pub if_body: FunctionBody,
    pub else_body: Option<FunctionBody>,
}

#[derive(Clone, Default)]
pub struct CaseBlock {
    pub position: Position,
    pub label: CaseLabel,
    pub body: FunctionBody,
}
#[derive(Clone, Default)]

pub struct CaseLabel {
    pub position: Position,
    pub enum_name: Identifier,
    pub enum_variant: Identifier,
    pub variables: Vec<Identifier>,
}

#[derive(Clone, Default)]
pub struct DefaultBlock {
    pub position: Position,
    pub body: FunctionBody,
}

#[derive(Clone, Default)]
pub struct EnumVariant {
    pub position: Position,
    pub name: Identifier,
    pub data: Vec<Type>,
}

#[derive(Clone, Default)]
pub struct Foreach {
    pub position: Position,
    pub body: FunctionBody,
}

#[derive(Clone, Default)]
pub struct FreeFunctionCall {
    pub position: Position,
    pub name: Identifier,
    pub parameters: Vec<Type>,
}

#[derive(Clone, Default)]
pub struct FreeFunctionName {
    pub position: Position,
    pub name: Identifier,
    pub parameters: Vec<Identifier>,
}

#[derive(Clone)]
pub enum FunctionBodyItem {
    Assignment(Assignment),
    Boolean(Boolean),
    Branch(Branch),
    CallByPointer(CallByPointer),
    Char(Char),
    Foreach(Foreach),
    FunctionCall(FunctionCall),
    FunctionType(FunctionType),
    GetField(GetField),
    GetFunction(GetFunction),
    Integer(Integer),
    Match(Match),
    Return(Return),
    SetField(SetField),
    String(ParsedString),
    Use(Use),
    While(While),
}

impl HasPosition for FunctionBodyItem {
    fn position(&self) -> Position {
        match self {
            Self::Assignment(item) => item.position.clone(),
            Self::Boolean(item) => item.position.clone(),
            Self::Branch(item) => item.position.clone(),
            Self::CallByPointer(item) => item.position.clone(),
            Self::Char(item) => item.position.clone(),
            Self::Foreach(item) => item.position.clone(),
            Self::FunctionCall(item) => item.position(),
            Self::FunctionType(item) => item.position.clone(),
            Self::GetField(item) => item.position.clone(),
            Self::GetFunction(item) => item.position.clone(),
            Self::Integer(item) => item.position.clone(),
            Self::Match(item) => item.position.clone(),
            Self::Return(item) => item.position.clone(),
            Self::SetField(item) => item.position.clone(),
            Self::String(item) => item.position.clone(),
            Self::Use(item) => item.position.clone(),
            Self::While(item) => item.position.clone(),
        }
    }
}

#[derive(Clone, Default)]
pub struct FunctionBody {
    pub position: Position,
    pub items: Vec<FunctionBodyItem>,
}

#[derive(Clone)]
pub enum FunctionCall {
    Member(MemberFunctionCall),
    Free(FreeFunctionCall),
}

impl FunctionCall {
    pub fn parameters(&self) -> &Vec<Type> {
        match self {
            Self::Free(free) => &free.parameters,
            Self::Member(member) => &member.parameters,
        }
    }
}

impl HasPosition for FunctionCall {
    fn position(&self) -> Position {
        match self {
            Self::Free(free) => free.position.clone(),
            Self::Member(member) => member.position.clone(),
        }
    }
}

#[derive(Clone, Default)]
pub struct Function {
    pub position: Position,
    pub name: FunctionName,
    pub arguments: Vec<Argument>,
    pub return_types: ReturnTypes,
    pub body: Option<FunctionBody>,
}

impl Function {
    pub fn name(&self) -> String {
        match &self.name {
            FunctionName::Free(free) => free.name.value.clone(),
            FunctionName::Member(member) => {
                format!("{}:{}", member.type_name.value, member.func_name.value)
            }
        }
    }
}

#[derive(Clone)]
pub enum FunctionName {
    Member(MemberFunctionName),
    Free(FreeFunctionName),
}

impl Default for FunctionName {
    fn default() -> Self {
        Self::Free(FreeFunctionName::default())
    }
}

impl FunctionName {
    pub fn type_name(&self) -> Option<String> {
        match &self {
            FunctionName::Free(_) => None,
            FunctionName::Member(member) => Some(member.type_name.value.clone()),
        }
    }
}

#[derive(Clone)]
pub struct GetFunction {
    pub position: Position,
    pub target: ParsedString,
}

impl GetFunction {
    pub fn new(token: &Token) -> Self {
        let target = ParsedString::new(token);
        Self {
            position: target.position.clone(),
            target,
        }
    }
}

#[derive(Clone, Default)]
pub struct ImportItem {
    pub position: Position,
    pub name: Identifier,
    pub alias: Option<Identifier>,
}

#[derive(Clone, Default)]
pub struct Import {
    pub position: Position,
    pub source: ParsedString,
    pub items: Vec<ImportItem>,
}

impl Import {
    pub fn get_source_path(&self, current_dir: &Path) -> PathBuf {
        let source = &self.source.value;

        if source.ends_with(".aaa") {
            let path = PathBuf::from(source);

            if path.is_absolute() {
                return path;
            }

            let path = self.position.path.parent().unwrap().join(source);

            return normalize_path(&path, current_dir);
        }

        let mut path = self
            .position
            .path
            .parent()
            .unwrap()
            .join(source.replace(".", MAIN_SEPARATOR_STR));

        path.set_extension("aaa");

        normalize_path(&path, current_dir)
    }
}

#[derive(Clone, Default)]
pub struct Match {
    pub position: Position,
    pub case_blocks: Vec<CaseBlock>,
    pub default_blocks: Vec<DefaultBlock>,
}

#[derive(Clone, Default)]
pub struct MemberFunctionCall {
    pub position: Position,
    pub type_name: Identifier,
    pub func_name: Identifier,
    pub parameters: Vec<Type>,
}

#[derive(Clone, Default)]
pub struct MemberFunctionName {
    pub position: Position,
    pub type_name: Identifier,
    pub func_name: Identifier,
    pub parameters: Vec<Identifier>,
}

#[derive(Clone)]
pub enum ReturnTypes {
    Never,
    Sometimes(Vec<Type>),
}

impl Default for ReturnTypes {
    fn default() -> Self {
        ReturnTypes::Sometimes(vec![])
    }
}

#[derive(Clone, Default)]
pub struct Struct {
    pub position: Position,
    pub name: Identifier,
    pub parameters: Vec<Identifier>,
    pub fields: Vec<StructField>,
    pub is_builtin: bool,
}

#[derive(Clone)]
pub struct GetField {
    pub position: Position,
    pub field_name: ParsedString,
}

impl GetField {
    pub fn new(token: &Token) -> Self {
        let field_name = ParsedString::new(token);
        Self {
            position: field_name.position.clone(),
            field_name,
        }
    }
}

#[derive(Clone)]
pub struct SetField {
    pub position: Position,
    pub field_name: ParsedString,
    pub body: FunctionBody,
}

impl SetField {
    pub fn new(token: &Token, body: FunctionBody) -> Self {
        let field_name = ParsedString::new(token);

        Self {
            position: field_name.position.clone(),
            field_name,
            body,
        }
    }
}

#[derive(Clone, Default)]
pub struct StructField {
    pub position: Position,
    pub name: Identifier,
    pub type_: Type,
}

#[derive(Clone, Default)]
pub struct RegularType {
    pub position: Position,

    #[allow(dead_code)] // TODO #216 Support const qualifier in Rust-based transpiler
    pub is_const: bool,

    pub name: Identifier,
    pub parameters: Vec<Type>,
}

#[derive(Clone, Default)]
pub struct FunctionType {
    pub position: Position,
    pub argument_types: Vec<Type>,
    pub return_types: ReturnTypes,
}

#[derive(Clone)]
pub enum Type {
    Regular(RegularType),
    Function(FunctionType),
}

impl HasPosition for Type {
    fn position(&self) -> Position {
        match self {
            Self::Function(function) => function.position.clone(),
            Self::Regular(regular) => regular.position.clone(),
        }
    }
}

impl Default for Type {
    fn default() -> Self {
        Self::Regular(RegularType::default())
    }
}

#[derive(Clone, Default)]
pub struct Use {
    pub position: Position,
    pub variables: Vec<Identifier>,
    pub body: FunctionBody,
}

#[derive(Clone, Default)]
pub struct While {
    pub position: Position,
    pub condition: FunctionBody,
    pub body: FunctionBody,
}

#[derive(Clone, Default)]
pub struct Identifier {
    pub position: Position,
    pub value: String,
}

#[derive(Clone)]
pub struct CallByPointer {
    pub position: Position,
}

#[derive(Clone)]
pub struct Char {
    pub position: Position,
    pub value: char,
}

impl Char {
    pub fn new(token: &Token) -> Self {
        let string = ParsedString::new(token);
        Self {
            position: token.position().clone(),
            value: string.value.chars().next().unwrap(),
        }
    }
}

#[derive(Clone)]
pub struct Integer {
    pub position: Position,
    pub value: isize,
}

impl Integer {
    pub fn new(token: &Token) -> Self {
        Self {
            position: token.position().clone(),
            value: token.value.parse().unwrap(),
        }
    }
}

#[derive(Clone)]
pub struct Return {
    pub position: Position,
}

#[derive(Clone, Default)]
pub struct ParsedString {
    pub position: Position,
    pub value: String,
}

impl ParsedString {
    pub fn new(token: &Token) -> Self {
        Self {
            position: token.position().clone(),
            value: unescape_string(&token.value[1..token.len() - 1]),
        }
    }
}

#[derive(Default, Clone)]
pub struct InterfaceFunction {
    pub position: Position,
    pub name: MemberFunctionName,
    pub arguments: Vec<Argument>,
    pub return_types: ReturnTypes,
}

#[derive(Default, Clone)]
pub struct Interface {
    pub position: Position,
    pub name: Identifier,
    pub functions: Vec<InterfaceFunction>,
    pub is_builtin: bool,
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
    use std::path::PathBuf;

    use crate::common::position::Position;

    use super::{unescape_string, Import, ParsedString};
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

    #[test]
    fn test_import_source_path_relative() {
        let current_dir = PathBuf::from("/home/user");

        let import = Import {
            position: Position::new("/bbb/ccc.aaa", 1, 1),
            source: ParsedString {
                position: Position::new("/bbb/ccc.aaa", 1, 1),
                value: String::from("ddd/eee.aaa"),
            },
            items: vec![],
        };

        let source_path = import.get_source_path(&current_dir);
        assert_eq!(source_path, PathBuf::from("/bbb/ddd/eee.aaa"));
    }

    #[test]
    fn test_import_source_path_absolute() {
        let current_dir = PathBuf::from("/home/user");

        let import = Import {
            position: Position::new("/bbb/ccc.aaa", 1, 1),
            source: ParsedString {
                position: Position::new("/bbb/ccc.aaa", 1, 1),
                value: String::from("/ddd/eee.aaa"),
            },
            items: vec![],
        };

        let source_path = import.get_source_path(&current_dir);
        assert_eq!(source_path, PathBuf::from("/ddd/eee.aaa"));
    }

    #[test]
    fn test_import_source_path_period_separated() {
        let current_dir = PathBuf::from("/home/user");

        let import = Import {
            position: Position::new("/bbb/ccc.aaa", 1, 1),
            source: ParsedString {
                position: Position::new("/bbb/ccc.aaa", 1, 1),
                value: String::from("ddd.eee"),
            },
            items: vec![],
        };

        let source_path = import.get_source_path(&current_dir);
        assert_eq!(source_path, PathBuf::from("/bbb/ddd/eee.aaa"));
    }
}
