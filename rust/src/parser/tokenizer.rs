use super::{
    position::Position,
    token::Token,
    token_type::{TokenType, ENUM_REGEX_PAIRS},
};

pub struct TokenizerError {
    pub position: Position,
}

impl TokenizerError {
    fn new(position: Position) -> Self {
        TokenizerError { position }
    }
}

pub fn tokenize(code: &str, file_name: Option<&str>) -> Result<Vec<Token>, TokenizerError> {
    let file_name = file_name.or(Some("/unknown/path.aaa")).unwrap();

    let mut tokens = vec![];
    let mut offset = 0;
    let mut position = Position::new(file_name.to_owned(), 1, 1);

    while offset < code.len() {
        match get_token(code, offset) {
            Some((type_, value)) => {
                let token = Token::new(type_, value, position.clone());
                offset += token.len();
                position = position.after(&token);
                tokens.push(token);
            }
            None => {
                return Err(TokenizerError::new(position));
            }
        }
    }

    Ok(tokens)
}

fn get_token(file_content: &str, offset: usize) -> Option<(TokenType, String)> {
    for (token_type, regex, group) in ENUM_REGEX_PAIRS.iter() {
        if let Some(captures) = regex.captures_at(file_content, offset) {
            let value = captures.get(*group).unwrap().as_str().to_owned();

            let substring = file_content.get(offset..offset + value.len());

            match substring {
                None => continue,
                Some(substring) => {
                    if substring != value {
                        continue;
                    }
                }
            }

            return Some((*token_type, value));
        }
    }

    None
}
