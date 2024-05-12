use super::{position::Position, token_type::TokenType};

#[derive(Debug, Clone)]
pub struct Token {
    pub type_: TokenType,
    pub value: String,
    pub position: Position,
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
}
