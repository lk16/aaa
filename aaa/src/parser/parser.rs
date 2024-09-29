use std::{fmt, vec};

use crate::{
    common::traits::HasPosition,
    parser::types::{GetField, GetFunction, ParsedString, SetField, Use},
    tokenizer::{types::Token, types::TokenType},
};

use super::types::{
    Argument, Assignment, Boolean, Branch, CallByPointer, CaseBlock, CaseLabel, Char, DefaultBlock,
    Enum, EnumVariant, Foreach, FreeFunctionCall, FreeFunctionName, Function, FunctionBody,
    FunctionBodyItem, FunctionCall, FunctionName, FunctionType, Identifier, Import, ImportItem,
    Integer, Match, MemberFunctionCall, MemberFunctionName, RegularType, Return, ReturnTypes,
    SourceFile, Struct, StructField, Type, While,
};

pub enum ParseError {
    UnexpectedToken(Token),
    UnexpectedEndOfFile(Option<Token>),
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match &self {
            ParseError::UnexpectedEndOfFile(last_token) => match last_token {
                Some(token) => write!(f, "{}: Unexpected end of file", token.end()),
                None => write!(f, "File is empty."),
            },
            ParseError::UnexpectedToken(token) => {
                write!(
                    f,
                    "{}: Unexpected token with type {:?}",
                    token.position(),
                    token.type_
                )
            }
        }
    }
}

pub fn parse(tokens: Vec<Token>) -> Result<SourceFile, ParseError> {
    Parser::new(tokens).parse()
}

type ParseResult<T> = Result<(T, usize), ParseError>;

struct Parser {
    tokens: Vec<Token>,
}

impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        Self { tokens }
    }

    fn parse(&self) -> Result<SourceFile, ParseError> {
        let (source_file, offset) = self.parse_source_file(0)?;
        if offset < self.tokens.len() {
            let unexpected = self.tokens[offset].clone();
            return Err(ParseError::UnexpectedToken(unexpected));
        }
        Ok(source_file)
    }

    fn peek_token(&self, offset: usize) -> Result<Token, ParseError> {
        match self.tokens.get(offset) {
            Some(token) => Ok(token.clone()),
            None => Err(ParseError::UnexpectedEndOfFile(self.tokens.last().cloned())),
        }
    }

    fn peek_token_type(&self, offset: usize) -> Option<TokenType> {
        self.peek_token(offset).ok().map(|token| token.type_)
    }

    fn parse_token(&self, offset: usize, expected_token_type: TokenType) -> ParseResult<Token> {
        let token = self.peek_token(offset)?;
        if token.type_ != expected_token_type {
            return Err(ParseError::UnexpectedToken(token));
        }
        Ok((token, offset + 1))
    }

    fn parse_comma_separated<T>(
        &self,
        mut offset: usize,
        parse_func: fn(&Parser, usize) -> ParseResult<T>,
    ) -> ParseResult<Vec<T>> {
        let mut items = vec![];
        let item;

        (item, offset) = parse_func(self, offset)?;
        items.push(item);

        while let Some(TokenType::Comma) = self.peek_token_type(offset) {
            offset += 1;

            let item;
            (item, offset) = match parse_func(self, offset) {
                Ok((item, offset)) => (item, offset),
                Err(_) => break,
            };
            items.push(item);
        }

        Ok((items, offset))
    }

    fn parse_source_file(&self, mut offset: usize) -> ParseResult<SourceFile> {
        let mut source_file = SourceFile::default();
        while offset < self.tokens.len() {
            let token = self.peek_token(offset)?;
            match token.type_ {
                TokenType::Enum => {
                    let enum_;
                    (enum_, offset) = self.parse_enum(offset)?;
                    source_file.enums.push(enum_);
                }
                TokenType::Struct => {
                    let struct_;
                    (struct_, offset) = self.parse_struct(offset)?;
                    source_file.structs.push(struct_);
                }
                TokenType::From => {
                    let import_;
                    (import_, offset) = self.parse_import(offset)?;
                    source_file.imports.push(import_);
                }
                TokenType::Fn => {
                    let (function, child_offset) = self.parse_function(offset)?;
                    offset = child_offset;
                    source_file.functions.push(function);
                }
                TokenType::Builtin => {
                    let next_token = self.peek_token(offset + 1)?;
                    match next_token.type_ {
                        TokenType::Struct => {
                            let struct_;
                            (struct_, offset) = self.parse_struct(offset)?;
                            source_file.structs.push(struct_);
                        }
                        TokenType::Enum => {
                            let enum_;
                            (enum_, offset) = self.parse_enum(offset)?;
                            source_file.enums.push(enum_);
                        }
                        TokenType::Fn => {
                            let (function, child_offset) = self.parse_function(offset)?;
                            offset = child_offset;
                            source_file.functions.push(function);
                        }
                        _ => return Err(ParseError::UnexpectedToken(token)),
                    }
                }
                _ => return Err(ParseError::UnexpectedToken(token)),
            }
        }
        Ok((source_file, offset))
    }

    fn parse_struct(&self, mut offset: usize) -> ParseResult<Struct> {
        let mut struct_ = Struct::default();

        let mut is_builtin = false;
        let mut builtin_token = None;

        if self.peek_token_type(offset) == Some(TokenType::Builtin) {
            let first_token;
            (first_token, offset) = self.parse_token(offset, TokenType::Builtin)?;
            builtin_token = Some(first_token);
            is_builtin = true;
        }

        let struct_token;
        (struct_token, offset) = self.parse_token(offset, TokenType::Struct)?;

        struct_.position = match builtin_token {
            Some(builtin_token) => builtin_token.position(),
            None => struct_token.position(),
        };

        (struct_.name, offset) = self.parse_identifier(offset)?;

        if self.peek_token_type(offset) == Some(TokenType::SqStart) {
            (struct_.parameters, offset) = self.parse_parameter_list(offset)?;
        }

        if !is_builtin {
            let fields;
            (fields, offset) = self.parse_struct_fields(offset)?;
            struct_.fields = Some(fields);
        }

        Ok((struct_, offset))
    }

    fn parse_identifier(&self, mut offset: usize) -> ParseResult<Identifier> {
        let token;
        let mut identifier = Identifier::default();

        (token, offset) = self.parse_token(offset, TokenType::Identifier)?;
        identifier.position = token.position();
        identifier.value = token.value;

        Ok((identifier, offset))
    }

    fn parse_parameter_list(&self, mut offset: usize) -> ParseResult<Vec<Identifier>> {
        let parameters;

        (_, offset) = self.parse_token(offset, TokenType::SqStart)?;
        (parameters, offset) = self.parse_comma_separated(offset, Parser::parse_identifier)?;
        (_, offset) = self.parse_token(offset, TokenType::SqEnd)?;

        Ok((parameters, offset))
    }

    fn parse_type_list(&self, mut offset: usize) -> ParseResult<Vec<Type>> {
        let types;

        (_, offset) = self.parse_token(offset, TokenType::SqStart)?;
        (types, offset) = self.parse_comma_separated(offset, Parser::parse_type)?;
        (_, offset) = self.parse_token(offset, TokenType::SqEnd)?;

        Ok((types, offset))
    }

    fn parse_struct_fields(&self, mut offset: usize) -> ParseResult<Vec<StructField>> {
        let mut struct_fields = vec![];

        (_, offset) = self.parse_token(offset, TokenType::Start)?;

        if self.peek_token_type(offset) != Some(TokenType::End) {
            (struct_fields, offset) =
                self.parse_comma_separated(offset, Parser::parse_struct_field)?;
        }

        (_, offset) = self.parse_token(offset, TokenType::End)?;

        Ok((struct_fields, offset))
    }

    fn parse_struct_field(&self, mut offset: usize) -> ParseResult<StructField> {
        let mut struct_field = StructField::default();

        (struct_field.name, offset) = self.parse_identifier(offset)?;
        struct_field.position = struct_field.name.position.clone();

        (_, offset) = self.parse_token(offset, TokenType::As)?;
        (struct_field.type_, offset) = self.parse_type(offset)?;

        Ok((struct_field, offset))
    }

    fn parse_type(&self, mut offset: usize) -> ParseResult<Type> {
        let type_ = match self.peek_token(offset)?.type_ {
            TokenType::Fn => {
                let function;
                (function, offset) = self.parse_function_type(offset)?;
                Type::Function(function)
            }
            _ => {
                let regular;
                (regular, offset) = self.parse_regular_type(offset)?;
                Type::Regular(regular)
            }
        };

        Ok((type_, offset))
    }

    fn parse_function_type_arguments(&self, mut offset: usize) -> ParseResult<Vec<Type>> {
        (_, offset) = self.parse_token(offset, TokenType::SqStart)?;

        if self.peek_token_type(offset) == Some(TokenType::SqEnd) {
            offset += 1;
            return Ok((vec![], offset));
        }

        let argument_types;
        (argument_types, offset) = self.parse_comma_separated(offset, Parser::parse_type)?;
        (_, offset) = self.parse_token(offset, TokenType::SqEnd)?;

        Ok((argument_types, offset))
    }

    fn parse_function_type_return_types(&self, mut offset: usize) -> ParseResult<ReturnTypes> {
        (_, offset) = self.parse_token(offset, TokenType::SqStart)?;

        if self.peek_token_type(offset) == Some(TokenType::SqEnd) {
            offset += 1;
            return Ok((ReturnTypes::Sometimes(vec![]), offset));
        }

        if self.peek_token_type(offset) == Some(TokenType::Never) {
            offset += 1;
            if self.peek_token_type(offset) == Some(TokenType::Comma) {
                offset += 1;
            }
            (_, offset) = self.parse_token(offset, TokenType::SqEnd)?;

            return Ok((ReturnTypes::Never, offset));
        }

        let sometimes;
        (sometimes, offset) = self.parse_comma_separated(offset, Parser::parse_type)?;
        (_, offset) = self.parse_token(offset, TokenType::SqEnd)?;

        Ok((ReturnTypes::Sometimes(sometimes), offset))
    }

    fn parse_function_type(&self, mut offset: usize) -> ParseResult<FunctionType> {
        let mut type_ = FunctionType::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::Fn)?;
        type_.position = first_token.position();

        (type_.argument_types, offset) = self.parse_function_type_arguments(offset)?;
        (type_.return_types, offset) = self.parse_function_type_return_types(offset)?;

        Ok((type_, offset))
    }

    fn parse_function_type_as_item(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let type_;
        (type_, offset) = self.parse_function_type(offset)?;
        let item = FunctionBodyItem::FunctionType(type_);
        Ok((item, offset))
    }

    fn parse_regular_type(&self, mut offset: usize) -> ParseResult<RegularType> {
        let mut type_ = RegularType::default();

        let mut const_token = None;

        if self.peek_token(offset)?.type_ == TokenType::Const {
            let first_token;
            (first_token, offset) = self.parse_token(offset, TokenType::Const)?;
            const_token = Some(first_token);
        }

        (type_.name, offset) = self.parse_identifier(offset)?;

        type_.position = match const_token {
            Some(const_token) => const_token.position(),
            None => type_.name.position.clone(),
        };

        if self.peek_token_type(offset) == Some(TokenType::SqStart) {
            offset += 1;
            (type_.parameters, offset) = self.parse_comma_separated(offset, Parser::parse_type)?;
            (_, offset) = self.parse_token(offset, TokenType::SqEnd)?;
        }

        Ok((type_, offset))
    }

    fn parse_function_return_types(&self, mut offset: usize) -> ParseResult<ReturnTypes> {
        (_, offset) = self.parse_token(offset, TokenType::Return)?;

        if self.peek_token_type(offset) == Some(TokenType::Never) {
            offset += 1;
            if self.peek_token_type(offset) == Some(TokenType::Comma) {
                offset += 1;
            }
            return Ok((ReturnTypes::Never, offset));
        }

        let types;
        (types, offset) = self.parse_comma_separated(offset, Parser::parse_type)?;

        Ok((ReturnTypes::Sometimes(types), offset))
    }

    fn parse_arguments(&self, mut offset: usize) -> ParseResult<Vec<Argument>> {
        (_, offset) = self.parse_token(offset, TokenType::Args)?;

        let arguments;
        (arguments, offset) = self.parse_comma_separated(offset, Parser::parse_argument)?;

        Ok((arguments, offset))
    }

    fn parse_function(&self, mut offset: usize) -> ParseResult<Function> {
        let mut function = Function::default();

        let mut is_builtin = false;

        let mut builtin_token = None;
        if self.peek_token_type(offset) == Some(TokenType::Builtin) {
            is_builtin = true;

            let first_token;
            (first_token, offset) = self.parse_token(offset, TokenType::Builtin)?;
            builtin_token = Some(first_token.position().clone());
        }

        let fn_token;
        (fn_token, offset) = self.parse_token(offset, TokenType::Fn)?;

        function.position = match builtin_token {
            Some(first_token) => first_token,
            None => fn_token.position().clone(),
        };

        (function.name, offset) = self.parse_function_name(offset)?;

        if self.peek_token_type(offset) == Some(TokenType::Args) {
            (function.arguments, offset) = self.parse_arguments(offset)?;
        }

        if self.peek_token_type(offset) == Some(TokenType::Return) {
            (function.return_types, offset) = self.parse_function_return_types(offset)?;
        }

        if !is_builtin {
            let body;
            (body, offset) = self.parse_function_body_block(offset)?;
            function.body = Some(body);
        }

        Ok((function, offset))
    }

    fn parse_function_name(&self, offset: usize) -> ParseResult<FunctionName> {
        match self.parse_member_function_name(offset) {
            Ok((member, offset)) => Ok((FunctionName::Member(member), offset)),
            Err(_) => match self.parse_free_function_name(offset) {
                Ok((free, offset)) => Ok((FunctionName::Free(free), offset)),
                Err(e) => Err(e),
            },
        }
    }

    fn parse_member_function_name(&self, mut offset: usize) -> ParseResult<MemberFunctionName> {
        let mut function_name = MemberFunctionName::default();

        (function_name.type_name, offset) = self.parse_identifier(offset)?;
        function_name.position = function_name.type_name.position.clone();

        if self.peek_token_type(offset) == Some(TokenType::SqStart) {
            (function_name.parameters, offset) = self.parse_parameter_list(offset)?;
        }

        (_, offset) = self.parse_token(offset, TokenType::Colon)?;

        if self.peek_token_type(offset) == Some(TokenType::Identifier) {
            (function_name.func_name, offset) = self.parse_identifier(offset)?;
        } else {
            (function_name.func_name, offset) = self.parse_operator_as_identifier(offset)?;
        }

        Ok((function_name, offset))
    }

    fn parse_free_function_name(&self, mut offset: usize) -> ParseResult<FreeFunctionName> {
        let mut function_name = FreeFunctionName::default();

        if self.peek_token_type(offset) == Some(TokenType::Operator) {
            (function_name.name, offset) = self.parse_operator_as_identifier(offset)?;
        } else {
            (function_name.name, offset) = self.parse_identifier(offset)?;
        }

        function_name.position = function_name.name.position.clone();

        if self.peek_token_type(offset) == Some(TokenType::SqStart) {
            (function_name.parameters, offset) = self.parse_parameter_list(offset)?;
        }

        Ok((function_name, offset))
    }

    fn parse_argument(&self, mut offset: usize) -> ParseResult<Argument> {
        let mut argument = Argument::default();

        (argument.name, offset) = self.parse_identifier(offset)?;
        argument.position = argument.name.position.clone();

        (_, offset) = self.parse_token(offset, TokenType::As)?;
        (argument.type_, offset) = self.parse_type(offset)?;

        Ok((argument, offset))
    }

    fn parse_function_body_block(&self, mut offset: usize) -> ParseResult<FunctionBody> {
        let function_body;

        (_, offset) = self.parse_token(offset, TokenType::Start)?;
        (function_body, offset) = self.parse_function_body(offset)?;
        (_, offset) = self.parse_token(offset, TokenType::End)?;

        Ok((function_body, offset))
    }

    fn parse_function_body(&self, mut offset: usize) -> ParseResult<FunctionBody> {
        let mut body = FunctionBody::default();

        loop {
            match self.parse_function_body_item(offset) {
                Ok((item, child_offset)) => {
                    body.items.push(item);
                    offset = child_offset;
                }
                Err(e) => {
                    if body.items.is_empty() {
                        return Err(e);
                    }
                    break;
                }
            }
        }

        body.position = body.items.first().unwrap().position();

        Ok((body, offset))
    }

    fn parse_function_body_item(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let token = self.peek_token(offset)?;

        let item;
        (item, offset) = match token.type_ {
            TokenType::Assign => self.parse_assignment(offset)?,
            TokenType::Call => self.parse_call(offset)?,
            TokenType::Char => self.parse_char(offset)?,
            TokenType::False => self.parse_boolean(offset)?,
            TokenType::Foreach => self.parse_foreach(offset)?,
            TokenType::Identifier => self.parse_function_body_item_with_identifier(offset)?,
            TokenType::If => self.parse_branch(offset)?,
            TokenType::Integer => self.parse_integer(offset)?,
            TokenType::Match => self.parse_match(offset)?,
            TokenType::Operator => self.parse_operator_as_item(offset)?,
            TokenType::Return => self.parse_return(offset)?,
            TokenType::String => self.parse_function_body_item_with_string(offset)?,
            TokenType::True => self.parse_boolean(offset)?,
            TokenType::Use => self.parse_use(offset)?,
            TokenType::While => self.parse_while(offset)?,
            TokenType::Fn => self.parse_function_type_as_item(offset)?,
            _ => return Err(ParseError::UnexpectedToken(token)),
        };

        Ok((item, offset))
    }

    fn parse_operator_as_identifier(&self, mut offset: usize) -> ParseResult<Identifier> {
        let token;
        (token, offset) = self.parse_token(offset, TokenType::Operator)?;

        let identifier = Identifier {
            value: token.value.clone(),
            position: token.position(),
        };
        Ok((identifier, offset))
    }

    fn parse_operator_as_item(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let mut call = FreeFunctionCall::default();
        (call.name, offset) = self.parse_operator_as_identifier(offset)?;
        call.position = call.name.position.clone();

        let item = FunctionBodyItem::FunctionCall(FunctionCall::Free(call));
        Ok((item, offset))
    }

    fn parse_branch(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let mut branch = Branch::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::If)?;
        branch.position = first_token.position();

        (branch.condition, offset) = self.parse_function_body(offset)?;
        (branch.if_body, offset) = self.parse_function_body_block(offset)?;

        if self.peek_token_type(offset) == Some(TokenType::Else) {
            offset += 1;
            let else_body;
            (else_body, offset) = self.parse_function_body_block(offset)?;
            branch.else_body = Some(else_body);
        }

        let item = FunctionBodyItem::Branch(branch);
        Ok((item, offset))
    }

    fn parse_function_body_item_with_identifier(
        &self,
        mut offset: usize,
    ) -> ParseResult<FunctionBodyItem> {
        match self.peek_token_type(offset + 1) {
            Some(TokenType::Comma) | Some(TokenType::Assign) => {
                let item;
                (item, offset) = self.parse_assignment(offset)?;
                return Ok((item, offset));
            }
            _ => (),
        }

        let call;
        (call, offset) = match self.parse_member_function_call(offset) {
            Ok((member, offset)) => (FunctionCall::Member(member), offset),
            Err(_) => match self.parse_free_function_call(offset) {
                Ok((free, offset)) => (FunctionCall::Free(free), offset),
                Err(e) => return Err(e),
            },
        };

        Ok((FunctionBodyItem::FunctionCall(call), offset))
    }

    fn parse_free_function_call(&self, mut offset: usize) -> ParseResult<FreeFunctionCall> {
        let mut call = FreeFunctionCall::default();

        (call.name, offset) = self.parse_identifier(offset)?;
        call.position = call.name.position.clone();

        if self.peek_token_type(offset) == Some(TokenType::SqStart) {
            offset += 1;
            (call.parameters, offset) = self.parse_comma_separated(offset, Parser::parse_type)?;
            (_, offset) = self.parse_token(offset, TokenType::SqEnd)?;
        }

        Ok((call, offset))
    }

    fn parse_member_function_call(&self, mut offset: usize) -> ParseResult<MemberFunctionCall> {
        let mut call = MemberFunctionCall::default();

        (call.type_name, offset) = self.parse_identifier(offset)?;
        call.position = call.type_name.position.clone();

        if self.peek_token_type(offset) == Some(TokenType::SqStart) {
            (call.parameters, offset) = self.parse_type_list(offset)?;
        }

        (_, offset) = self.parse_token(offset, TokenType::Colon)?;
        (call.func_name, offset) = self.parse_identifier(offset)?;
        if call.parameters.is_empty() && self.peek_token_type(offset) == Some(TokenType::SqStart) {
            (call.parameters, offset) = self.parse_type_list(offset)?;
        }

        Ok((call, offset))
    }

    fn parse_call(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::Call)?;

        let call = CallByPointer {
            position: first_token.position(),
        };

        Ok((FunctionBodyItem::CallByPointer(call), offset))
    }

    fn parse_char(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let token;
        (token, offset) = self.parse_token(offset, TokenType::Char)?;
        Ok((FunctionBodyItem::Char(Char::new(&token)), offset))
    }

    fn parse_integer(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let token;
        (token, offset) = self.parse_token(offset, TokenType::Integer)?;
        Ok((FunctionBodyItem::Integer(Integer::new(&token)), offset))
    }

    fn parse_return(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::Return)?;

        let return_ = Return {
            position: first_token.position(),
        };

        Ok((FunctionBodyItem::Return(return_), offset))
    }

    fn parse_assignment(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let mut assignment = Assignment::default();

        (assignment.variables, offset) =
            self.parse_comma_separated(offset, Parser::parse_identifier)?;

        assignment.position = assignment.variables[0].position.clone();

        (_, offset) = self.parse_token(offset, TokenType::Assign)?;
        (assignment.body, offset) = self.parse_function_body_block(offset)?;
        Ok((FunctionBodyItem::Assignment(assignment), offset))
    }

    fn parse_boolean(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let token = self.peek_token(offset)?;
        match token.type_ {
            TokenType::True | TokenType::False => (),
            _ => return Err(ParseError::UnexpectedToken(token)),
        }

        offset += 1;
        Ok((FunctionBodyItem::Boolean(Boolean::new(&token)), offset))
    }

    fn parse_foreach(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let mut foreach = Foreach::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::Foreach)?;
        foreach.position = first_token.position();

        (foreach.body, offset) = self.parse_function_body_block(offset)?;
        Ok((FunctionBodyItem::Foreach(foreach), offset))
    }

    fn parse_function_body_item_with_string(
        &self,
        mut offset: usize,
    ) -> ParseResult<FunctionBodyItem> {
        let item;
        (item, offset) = match self.peek_token_type(offset + 1) {
            Some(TokenType::GetField) => self.parse_get_field(offset)?,
            Some(TokenType::Start) => self.parse_set_field(offset)?,
            Some(TokenType::Fn) => self.parse_get_function(offset)?,
            _ => self.parse_string_as_item(offset)?,
        };

        Ok((item, offset))
    }

    fn parse_get_field(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let token;
        (token, offset) = self.parse_token(offset, TokenType::String)?;
        (_, offset) = self.parse_token(offset, TokenType::GetField)?;

        let item = FunctionBodyItem::GetField(GetField::new(&token));
        Ok((item, offset))
    }

    fn parse_set_field(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let body;
        let token;

        (token, offset) = self.parse_token(offset, TokenType::String)?;
        (body, offset) = self.parse_function_body_block(offset)?;
        (_, offset) = self.parse_token(offset, TokenType::SetField)?;

        let item = FunctionBodyItem::SetField(SetField::new(&token, body));
        Ok((item, offset))
    }

    fn parse_get_function(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let token;
        (token, offset) = self.parse_token(offset, TokenType::String)?;
        (_, offset) = self.parse_token(offset, TokenType::Fn)?;

        let item = FunctionBodyItem::GetFunction(GetFunction::new(&token));
        Ok((item, offset))
    }

    fn parse_string(&self, mut offset: usize) -> ParseResult<ParsedString> {
        let token;
        (token, offset) = self.parse_token(offset, TokenType::String)?;

        Ok((ParsedString::new(&token), offset))
    }

    fn parse_string_as_item(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let string;
        (string, offset) = self.parse_string(offset)?;
        let item = FunctionBodyItem::String(string);
        Ok((item, offset))
    }

    fn parse_match(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let mut match_ = Match::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::Match)?;
        match_.position = first_token.position();

        (_, offset) = self.parse_token(offset, TokenType::Start)?;

        loop {
            let token = self.peek_token(offset)?;
            match token.type_ {
                TokenType::Case => {
                    let case_;
                    (case_, offset) = self.parse_case(offset)?;
                    match_.case_blocks.push(case_);
                }
                TokenType::Default => {
                    let default;
                    (default, offset) = self.parse_default(offset)?;
                    match_.default_blocks.push(default);
                }
                TokenType::End => {
                    if match_.default_blocks.is_empty() && match_.case_blocks.is_empty() {
                        return Err(ParseError::UnexpectedToken(token));
                    }

                    offset += 1;
                    break;
                }
                _ => return Err(ParseError::UnexpectedToken(token)),
            }
        }

        Ok((FunctionBodyItem::Match(match_), offset))
    }

    fn parse_case(&self, mut offset: usize) -> ParseResult<CaseBlock> {
        let mut case_ = CaseBlock::default();

        (case_.label, offset) = self.parse_case_label(offset)?;
        case_.position = case_.label.position.clone();

        (case_.body, offset) = self.parse_function_body_block(offset)?;

        Ok((case_, offset))
    }

    fn parse_case_label(&self, mut offset: usize) -> ParseResult<CaseLabel> {
        let mut label = CaseLabel::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::Case)?;
        label.position = first_token.position();

        (label.enum_name, offset) = self.parse_identifier(offset)?;
        (_, offset) = self.parse_token(offset, TokenType::Colon)?;
        (label.enum_variant, offset) = self.parse_identifier(offset)?;

        if self.peek_token_type(offset) == Some(TokenType::As) {
            offset += 1;
            (label.variables, offset) =
                self.parse_comma_separated(offset, Parser::parse_identifier)?;
        }

        Ok((label, offset))
    }

    fn parse_default(&self, mut offset: usize) -> ParseResult<DefaultBlock> {
        let mut default = DefaultBlock::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::Default)?;
        default.position = first_token.position();

        (default.body, offset) = self.parse_function_body_block(offset)?;

        Ok((default, offset))
    }

    fn parse_use(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let mut use_ = Use::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::Use)?;
        use_.position = first_token.position();

        (use_.variables, offset) = self.parse_comma_separated(offset, Parser::parse_identifier)?;
        (use_.body, offset) = self.parse_function_body_block(offset)?;

        let item = FunctionBodyItem::Use(use_);
        Ok((item, offset))
    }

    fn parse_while(&self, mut offset: usize) -> ParseResult<FunctionBodyItem> {
        let mut while_ = While::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::While)?;
        while_.position = first_token.position();

        (while_.condition, offset) = self.parse_function_body(offset)?;
        (while_.body, offset) = self.parse_function_body_block(offset)?;

        let item = FunctionBodyItem::While(while_);
        Ok((item, offset))
    }

    fn parse_enum(&self, mut offset: usize) -> ParseResult<Enum> {
        let mut enum_ = Enum::default();

        let mut builtin_token = None;

        if self.peek_token_type(offset) == Some(TokenType::Builtin) {
            let first_token;
            (first_token, offset) = self.parse_token(offset, TokenType::Builtin)?;
            builtin_token = Some(first_token);
            enum_.is_builtin = true;
        }

        let enum_token;
        (enum_token, offset) = self.parse_token(offset, TokenType::Enum)?;

        enum_.position = match builtin_token {
            Some(builtin_token) => builtin_token.position(),
            None => enum_token.position(),
        };

        (enum_.name, offset) = self.parse_identifier(offset)?;

        if self.peek_token_type(offset) == Some(TokenType::SqStart) {
            (enum_.parameters, offset) = self.parse_parameter_list(offset)?;
        }

        (_, offset) = self.parse_token(offset, TokenType::Start)?;
        (enum_.variants, offset) =
            self.parse_comma_separated(offset, Parser::parse_enum_variant)?;
        (_, offset) = self.parse_token(offset, TokenType::End)?;

        Ok((enum_, offset))
    }

    fn parse_enum_variant(&self, mut offset: usize) -> ParseResult<EnumVariant> {
        let mut variant = EnumVariant::default();

        (variant.name, offset) = self.parse_identifier(offset)?;
        variant.position = variant.name.position.clone();

        if self.peek_token_type(offset) == Some(TokenType::As) {
            (variant.data, offset) = self.parse_enum_variant_data(offset)?;
        }

        Ok((variant, offset))
    }

    fn parse_enum_variant_data(&self, mut offset: usize) -> ParseResult<Vec<Type>> {
        (_, offset) = self.parse_token(offset, TokenType::As)?;

        if self.peek_token_type(offset) != Some(TokenType::Start) {
            let data_item;
            (data_item, offset) = self.parse_type(offset)?;
            return Ok((vec![data_item], offset));
        }

        let data;

        (_, offset) = self.parse_token(offset, TokenType::Start)?;
        (data, offset) = self.parse_comma_separated(offset, Parser::parse_type)?;
        (_, offset) = self.parse_token(offset, TokenType::End)?;

        Ok((data, offset))
    }

    fn parse_import(&self, mut offset: usize) -> ParseResult<Import> {
        let mut import_ = Import::default();

        let first_token;
        (first_token, offset) = self.parse_token(offset, TokenType::From)?;
        import_.position = first_token.position().clone();

        (import_.source, offset) = self.parse_string(offset)?;
        (_, offset) = self.parse_token(offset, TokenType::Import)?;
        (import_.items, offset) = self.parse_comma_separated(offset, Parser::parse_import_item)?;

        Ok((import_, offset))
    }

    fn parse_import_item(&self, mut offset: usize) -> ParseResult<ImportItem> {
        let mut item = ImportItem::default();

        (item.name, offset) = self.parse_identifier(offset)?;
        item.position = item.name.position.clone();

        if self.peek_token_type(offset) == Some(TokenType::As) {
            offset += 1;
            let alias;
            (alias, offset) = self.parse_identifier(offset)?;
            item.alias = Some(alias);
        }

        Ok((item, offset))
    }
}

#[cfg(test)]
mod tests {
    use std::fs;

    use rstest::rstest;

    use crate::{
        common::files::find_aaa_files,
        parser::types::FunctionBodyItem,
        tokenizer::{tokenizer::tokenize_filtered, types::Token},
    };

    use super::{parse, ParseResult, Parser};

    fn parse_as<T>(code: &str, parse_func: fn(&Parser, usize) -> ParseResult<T>) -> T {
        let tokens = tokenize_filtered(code, None).unwrap();
        let parser = Parser::new(tokens.clone());
        let Ok((parsed, offset)) = parse_func(&parser, 0) else {
            unreachable!()
        };
        assert_eq!(offset, tokens.len());
        parsed
    }

    fn check_parse<T>(
        code: &str,
        expected_parsed_ok: bool,
        parse_func: fn(&Parser, usize) -> ParseResult<T>,
    ) {
        let tokens = tokenize_filtered(code, None).unwrap();
        let parser = Parser::new(tokens.clone());
        let parse_result = parse_func(&parser, 0);

        fn print_tokens(tokens: &Vec<Token>) {
            println!();
            for (offset, token) in tokens.iter().enumerate() {
                println!("offset {} = {:?}", offset, token);
            }
            println!();
        }

        match parse_result {
            Ok((_, offset)) => {
                if expected_parsed_ok && (offset != tokens.len()) {
                    print_tokens(&tokens);
                    println!("Not all tokens were consumed:");
                    println!("Available tokens: {}", tokens.len());
                    println!(" Consumed tokens: {}", offset);
                    assert!(false);
                }

                if !expected_parsed_ok && (offset == tokens.len()) {
                    print_tokens(&tokens);
                    println!("Parsing succeedeed unexpectedly!");
                    assert!(false);
                }
            }
            Err(err) => {
                if expected_parsed_ok {
                    print_tokens(&tokens);
                    println!("Parse error: {}", err);
                    println!("Parsing failed unexpectedly!");
                    assert!(false);
                }
            }
        }
    }

    #[rstest]
    #[case("true", true)]
    #[case("false", true)]
    #[case("", false)]
    #[case("falsex", false)]
    #[case("false{", false)]
    #[case("truex", false)]
    #[case("true{", false)]
    #[case("3", false)]
    fn test_parse_boolean(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_boolean);
    }

    #[rstest]
    #[case("true", true)]
    #[case("false", false)]
    fn test_parse_boolean_value(#[case] code: &str, #[case] expected_value: bool) {
        let parsed = parse_as(code, Parser::parse_boolean);
        match parsed {
            FunctionBodyItem::Boolean(boolean) => {
                assert_eq!(boolean.value, expected_value);
            }
            _ => unreachable!(),
        }
    }

    #[rstest]
    #[case("0", true)]
    #[case("9", true)]
    #[case("-0", true)]
    #[case("-9", true)]
    #[case("99999999", true)]
    #[case("00000000", true)]
    #[case("-99999999", true)]
    #[case("-00000000", true)]
    #[case("a9", false)]
    #[case("9a", false)]
    #[case("", false)]
    #[case("foo", false)]
    fn test_parse_integer(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_integer);
    }

    #[rstest]
    #[case("0", 0)]
    #[case("9", 9)]
    #[case("-0", 0)]
    #[case("-9", -9)]
    #[case("99999999", 99999999)]
    #[case("00000000", 0)]
    #[case("-99999999", -99999999)]
    #[case("-00000000", 0)]
    fn test_parse_integer_value(#[case] code: &str, #[case] expected_value: isize) {
        let parsed = parse_as(code, Parser::parse_integer);
        match parsed {
            FunctionBodyItem::Integer(integer) => {
                assert_eq!(integer.value, expected_value);
            }
            _ => unreachable!(),
        }
    }

    #[rstest]
    #[case("\"\"", true)]
    #[case("\"foo\"", true)]
    #[case("\"fn\"", true)]
    #[case("\"9\"", true)]
    #[case("\"\\n\"", true)]
    #[case("", false)]
    #[case("foo", false)]
    fn test_parse_string(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_string);
    }

    #[rstest]
    #[case("\"\"", "")]
    #[case("\"foo\"", "foo")]
    #[case("\"fn\"", "fn")]
    #[case("\"9\"", "9")]
    #[case("\"\\n\"", "\n")]
    fn test_parse_string_value(#[case] code: &str, #[case] expected_value: &str) {
        let string = parse_as(code, Parser::parse_string);
        assert_eq!(string.value, expected_value);
    }

    #[rstest]
    #[case("'a'", true)]
    #[case("'\\n'", true)]
    #[case("'9'", true)]
    #[case("3", false)]
    #[case("", false)]
    fn test_parse_char(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_char);
    }

    #[rstest]
    #[case("'a'", 'a')]
    #[case("'\\n'", '\n')]
    #[case("'9'", '9')]
    fn test_parse_char_value(#[case] code: &str, #[case] expected_value: char) {
        let parsed = parse_as(code, Parser::parse_char);
        match parsed {
            FunctionBodyItem::Char(char_) => {
                assert_eq!(char_.value, expected_value);
            }
            _ => unreachable!(),
        }
    }

    #[rstest]
    #[case("call", true)]
    #[case("3", false)]
    #[case("", false)]
    fn test_parse_call(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_call);
    }

    #[rstest]
    #[case("return", true)]
    #[case("3", false)]
    #[case("", false)]
    fn test_parse_return(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_return);
    }

    fn parse_comma_separated_integers(
        parser: &Parser,
        offset: usize,
    ) -> ParseResult<Vec<FunctionBodyItem>> {
        return parser.parse_comma_separated(offset, Parser::parse_integer);
    }

    #[rstest]
    #[case("", false)]
    #[case("1", true)]
    #[case("1,", true)]
    #[case("1,2", true)]
    #[case("1,2,", true)]
    #[case("1,false", false)]
    fn test_parse_comma_separated(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, parse_comma_separated_integers);
    }

    #[rstest]
    #[case("1", vec![1])]
    #[case("1,", vec![1])]
    #[case("1,2", vec![1,2])]
    #[case("1,2,", vec![1,2])]
    fn parse_comma_separated_values(#[case] code: &str, #[case] expected_integers: Vec<isize>) {
        let parsed = parse_as(code, parse_comma_separated_integers);
        let mut integers = vec![];

        for parsed_item in parsed.iter() {
            let integer = match parsed_item {
                FunctionBodyItem::Integer(integer) => integer.value,
                _ => unreachable!(),
            };
            integers.push(integer);
        }

        assert_eq!(integers, expected_integers);
    }

    #[rstest]
    #[case("", false)]
    #[case("\"foo\" ?", true)]
    #[case("\"\" ?", true)]
    #[case("\"\"", false)]
    #[case("?", false)]
    fn test_parse_get_field(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_get_field);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo", true)]
    #[case("foo[A]", true)]
    #[case("foo[A,]", true)]
    #[case("foo[A,B]", true)]
    #[case("foo[A,B,]", true)]
    #[case("foo[foo[A],B,]", true)]
    #[case("foo[]", false)]
    fn test_parse_regular_type(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_regular_type);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo", true)]
    #[case("foo[int]", true)]
    #[case("foo[int,]", true)]
    #[case("foo[int,int]", true)]
    #[case("foo[int,int,]", true)]
    #[case("foo[int,int,]", true)]
    #[case("foo[foo[int],int,]", true)]
    #[case("foo[]", false)]
    fn test_parse_free_function_call(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_free_function_call);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo", false)]
    #[case("foo:", false)]
    #[case(":bar", false)]
    #[case("foo:bar", true)]
    #[case("foo[int]:bar", true)]
    #[case("foo[int,]:bar", true)]
    #[case("foo[int,int]:bar", true)]
    #[case("foo[int,int,]:bar", true)]
    #[case("foo[foo[int],int,]:bar", true)]
    #[case("foo:bar[int]", true)]
    #[case("foo:bar[int,]", true)]
    #[case("foo:bar[int,int]", true)]
    #[case("foo:bar[int,int,]", true)]
    #[case("foo:bar[foo[int],int,]", true)]
    #[case("foo[]", false)]
    fn test_parse_member_function_call(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_member_function_call);
    }

    #[rstest]
    #[case("", false)]
    #[case("\"foo\" fn", true)]
    #[case("\"foo:bar\" fn", true)]
    #[case("\"foo\"", false)]
    #[case("\"foo:bar\"", false)]
    #[case("fn", false)]
    fn test_parse_call_get_function(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_get_function);
    }

    #[rstest]
    #[case("", false)]
    #[case("a <- { true }", true)]
    #[case("if true { nop }", true)]
    #[case("true", true)]
    #[case("call", true)]
    #[case("foreach { nop }", true)]
    #[case("foo:bar", true)]
    #[case("fn[int][bool]", true)]
    #[case("\"foo\" fn", true)]
    #[case("3", true)]
    #[case("match { default { nop } }", true)]
    #[case("return", true)]
    #[case("\"foo\" ?", true)]
    #[case("\"foo\" { 3 } !", true)]
    #[case("use a { nop }", true)]
    #[case("while true { nop }", true)]
    #[case("\"foo\"", true)]
    fn test_parse_function_body_item(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_function_body_item);
    }

    #[rstest]
    #[case("", false)]
    #[case("if true { nop }", true)]
    #[case("if true { nop } else { nop }", true)]
    #[case("if true { }", false)]
    #[case("if { nop }", false)]
    #[case("if true { nop } else { }", false)]
    fn test_parse_branch(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_branch);
    }

    #[rstest]
    #[case("", false)]
    #[case("use a { nop }", true)]
    #[case("use a, { nop }", true)]
    #[case("use a,b { nop }", true)]
    #[case("use a,b, { nop }", true)]
    #[case("use { nop }", false)]
    #[case("use a { }", false)]
    fn test_parse_use(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_use);
    }

    #[rstest]
    #[case("", false)]
    #[case("while true { nop }", true)]
    #[case("while true true and { nop }", true)]
    #[case("while { nop }", false)]
    #[case("while true { }", false)]
    fn test_parse_while(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_while);
    }

    #[rstest]
    #[case("", false)]
    #[case("a <- { nop }", true)]
    #[case("a, <- { nop }", true)]
    #[case("a,b <- { nop }", true)]
    #[case("a,b, <- { nop }", true)]
    #[case("<- { nop }", false)]
    #[case("a <- { }", false)]
    fn test_parse_assignment(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_assignment);
    }

    #[rstest]
    #[case("", false)]
    #[case("foreach { nop }", true)]
    #[case("foreach { nop nop }", true)]
    #[case("foreach { }", false)]
    fn test_parse_foreach(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_foreach);
    }

    #[rstest]
    #[case("", false)]
    #[case("\"foo\" { 3 } !", true)]
    #[case("\"foo\" { 3 1 + } !", true)]
    #[case("\"foo\" { } !", false)]
    #[case("\"foo\" !", false)]
    fn test_parse_set_field(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_set_field);
    }

    #[rstest]
    #[case("", false)]
    #[case("case foo:bar", true)]
    #[case("case foo:bar as baz", true)]
    #[case("case foo:bar as baz,", true)]
    #[case("case foo:bar as baz,quux", true)]
    #[case("case foo:bar as baz,quux,", true)]
    #[case("case foo[int]:bar", false)]
    #[case("case :bar", false)]
    #[case("case foo:", false)]
    fn test_parse_case_label(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_case_label);
    }

    #[rstest]
    #[case("", false)]
    #[case("case foo:bar { nop }", true)]
    #[case("case foo:bar { }", false)]
    fn test_parse_case(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_case);
    }

    #[rstest]
    #[case("", false)]
    #[case("default { nop }", true)]
    #[case("default { }", false)]
    fn test_parse_default(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_default);
    }

    #[rstest]
    #[case("", false)]
    #[case("match { default { nop } }", true)]
    #[case("match { case foo:bar { nop } }", true)]
    #[case("match { case foo:bar { nop } default { nop } }", true)]
    #[case("match { }", false)]
    fn test_parse_match(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_match);
    }

    #[rstest]
    #[case("", false)]
    #[case("fn[][]", true)]
    #[case("fn[int][]", true)]
    #[case("fn[int,][]", true)]
    #[case("fn[int,][]", true)]
    #[case("fn[int,int,][]", true)]
    #[case("fn[][int]", true)]
    #[case("fn[][int,]", true)]
    #[case("fn[][int,]", true)]
    #[case("fn[][int,int,]", true)]
    #[case("fn[][never]", true)]
    #[case("fn[][never,]", true)]
    #[case("fn[never][]", false)]
    #[case("fn[int][int]", true)]
    #[case("fn[int,][int]", true)]
    #[case("fn[int][int,]", true)]
    #[case("fn[int,][int,]", true)]
    fn test_parse_function_type(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_function_type);
    }

    #[rstest]
    #[case("", false)]
    #[case("[]", false)]
    #[case("[A]", true)]
    #[case("[A,]", true)]
    #[case("[A,B]", true)]
    #[case("[A,B,]", true)]
    #[case("[A[B]]", false)]
    #[case("[A[B],A[B]]", false)]
    #[case("[A[B],A[B],]", false)]
    fn test_parse_parameter_list(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_parameter_list);
    }

    #[rstest]
    #[case("", false)]
    #[case("[]", false)]
    #[case("[A]", true)]
    #[case("[A,]", true)]
    #[case("[A,B]", true)]
    #[case("[A,B,]", true)]
    #[case("[A[B]]", true)]
    #[case("[A[B],A[B]]", true)]
    #[case("[A[B],A[B],]", true)]
    fn test_parse_type_list(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_type_list);
    }

    #[rstest]
    #[case("", false)]
    #[case("a <- { true } a <- { true }", true)]
    #[case("if true { nop } if true { nop }", true)]
    #[case("true true", true)]
    #[case("call call", true)]
    #[case("foreach { nop } foreach { nop }", true)]
    #[case("foo:bar foo:bar", true)]
    #[case("fn[int][bool] fn[int][bool]", true)]
    #[case("\"foo\" fn \"foo\" fn", true)]
    #[case("3 3", true)]
    #[case("match { default { nop } } match { default { nop } }", true)]
    #[case("return return", true)]
    #[case("\"foo\" ? \"foo\" ?", true)]
    #[case("\"foo\" { 3 } ! \"foo\" { 3 } !", true)]
    #[case("use a { nop } use a { nop }", true)]
    #[case("while true { nop } while true { nop }", true)]
    #[case("\"foo\" \"foo\"", true)]
    fn test_parse_function_body(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_function_body);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo as int", true)]
    #[case("foo as vec[int]", true)]
    #[case("foo as vec[int,]", true)]
    #[case("foo as map[int,int]", true)]
    #[case("foo as map[int,int,]", true)]
    #[case("foo[bar] as int", false)]
    #[case("foo as never", false)]
    #[case("foo as", false)]
    #[case("as int", false)]
    fn test_parse_argument(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_argument);
    }

    #[rstest]
    #[case("", false)]
    #[case("args", false)]
    #[case("args foo as int", true)]
    #[case("args foo as int,", true)]
    #[case("args foo as vec[int]", true)]
    #[case("args foo as vec[int],", true)]
    #[case("args foo as int, foo as int", true)]
    #[case("args foo as int, foo as int,", true)]
    #[case("args foo as vec[int], foo as vec[int]", true)]
    #[case("args foo as vec[int], foo as vec[int],", true)]
    #[case("args foo[bar] as int", false)]
    #[case("args foo as never", false)]
    #[case("args foo as", false)]
    #[case("args as int", false)]
    fn test_parse_arguments(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_arguments);
    }

    #[rstest]
    #[case("", false)]
    #[case("return", false)]
    #[case("return int", true)]
    #[case("return int,", true)]
    #[case("return int,int", true)]
    #[case("return vec[int]", true)]
    #[case("return vec[int],", true)]
    #[case("return vec[int],int", true)]
    #[case("return never", true)]
    #[case("return never,", true)]
    #[case("return never,int", false)]
    fn test_parse_function_return_types(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_function_return_types);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo", true)]
    #[case("foo[]", false)]
    #[case("foo:bar", false)]
    #[case("foo[A]", true)]
    #[case("=[A]", true)]
    #[case("foo[vec[int]]", false)]
    fn test_parse_free_function_name(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_free_function_name);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo:", false)]
    #[case(":bar", false)]
    #[case("foo:bar", true)]
    #[case("foo:=", true)]
    #[case("foo:bar[]", false)]
    #[case("foo[]:bar", false)]
    #[case("foo[A]:bar", true)]
    #[case("foo:bar[A]", false)]
    #[case("foo[vec[int]]:bar", false)]
    #[case("foo:bar[vec[int]]", false)]
    fn test_parse_member_function_name(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_member_function_name);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo", true)]
    #[case("_", true)]
    #[case("foo_", true)]
    #[case("Foo", true)]
    fn test_parse_identifier(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_identifier);
    }

    #[rstest]
    #[case("", false)]
    #[case("fn foo { nop }", true)]
    #[case("builtin fn foo", true)]
    #[case("builtin fn foo { nop } ", false)]
    #[case("fn foo args a as int, b as bool return str { nop }", true)]
    #[case("builtin fn foo args a as int, b as bool return str", true)]
    #[case("builtin fn foo args a as int, b as bool return str { nop }", false)]
    #[case("fn foo[A]:bar { match { default { nop } } }", true)]
    #[case("fn foo { 3 5 + if true { nop } while false { 69 } }", true)]

    fn test_parse_function(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_function);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo as int", true)]
    #[case("foo as vec[int]", true)]
    #[case("foo as vec[int,]", true)]
    #[case("foo as vec[map[int,int]]", true)]
    #[case("foo as vec[map[int,int,]]", true)]
    #[case("foo as vec[map[int,int],]", true)]
    #[case("foo as vec[map[int,int,],]", true)]
    #[case("foo as fn[int][int]", true)]
    #[case("foo as never", false)]
    #[case("foo as", false)]
    #[case("as int", false)]
    fn test_parse_struct_field(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_struct_field);
    }

    #[rstest]
    #[case("", false)]
    #[case("builtin struct foo", true)]
    #[case("builtin struct foo { }", false)]
    #[case("builtin struct foo[A]", true)]
    #[case("builtin struct foo[A,]", true)]
    #[case("builtin struct foo[A,B]", true)]
    #[case("builtin struct foo[A,B,]", true)]
    #[case("builtin struct foo[A,B,]", true)]
    #[case("struct foo { }", true)]
    #[case("struct foo", false)]
    #[case("struct foo[A] { }", true)]
    #[case("struct foo[A,] { }", true)]
    #[case("struct foo[A,B] { }", true)]
    #[case("struct foo[A,B,] { }", true)]
    #[case("struct foo { foo as bar }", true)]
    #[case("struct foo { foo as bar, }", true)]
    #[case("struct foo { foo as vec[int] }", true)]
    #[case("struct foo { foo as vec[int], }", true)]
    #[case("struct foo { foo as map[int,int], }", true)]
    #[case("struct foo { foo as map[int,int], foo as map[int,int], }", true)]
    fn test_parse_struct(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_struct);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo", true)]
    #[case("foo as int", true)]
    #[case("foo as vec[int]", true)]
    #[case("foo as vec[int,]", true)]
    #[case("foo as { int }", true)]
    #[case("foo as { int, }", true)]
    #[case("foo as { vec[int] }", true)]
    #[case("foo as { vec[int,] }", true)]
    #[case("foo as { vec[int,], }", true)]
    #[case("foo as { vec[int,], vec[int] }", true)]
    fn test_parse_enum_variant(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_enum_variant);
    }

    #[rstest]
    #[case("", false)]
    #[case("enum foo { bar }", true)]
    #[case("enum foo { bar as int }", true)]
    #[case("enum foo { bar as int, }", true)]
    #[case("enum foo { bar as fn[int][int] }", true)]
    #[case("enum foo { bar as fn[int][int], }", true)]
    #[case("enum foo { bar as vec[int], }", true)]
    #[case("enum foo { bar as vec[int], baz }", true)]
    fn test_parse_enum(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_enum);
    }

    #[rstest]
    #[case("", false)]
    #[case("foo", true)]
    #[case("foo as bar", true)]
    #[case("foo as", false)]
    #[case("as bar", false)]
    fn test_parse_import_item(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_import_item);
    }

    #[rstest]
    #[case("", false)]
    #[case("from \"file\" import foo", true)]
    #[case("from \"file\" import foo,", true)]
    #[case("from \"file\" import foo as bar", true)]
    #[case("from \"file\" import foo as bar,", true)]
    #[case("from \"file\" import foo, baz", true)]
    #[case("from \"file\" import foo, baz,", true)]
    fn test_parse_import(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_import);
    }

    #[rstest]
    #[case("", true)]
    #[case("from \"file\" import foo", true)]
    #[case("enum foo { bar as int }", true)]
    #[case("struct foo { bar as int }", true)]
    #[case("fn foo { bar }", true)]
    fn test_parse_source_file(#[case] code: &str, #[case] expected_parsed: bool) {
        check_parse(code, expected_parsed, Parser::parse_source_file);
    }

    #[test]
    fn test_parse_all_files() {
        for path in find_aaa_files().iter() {
            let code = fs::read_to_string(path).unwrap();
            let tokens = tokenize_filtered(&code, Some(path.clone())).unwrap();
            match parse(tokens) {
                Ok(_) => (),
                Err(e) => {
                    println!("Failed to parse {:?}", path);
                    println!("{}", e);
                    assert!(false);
                }
            }
        }
    }
}
