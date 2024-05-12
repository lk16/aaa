use super::{position::Position, token_type::TokenType};

#[derive(Debug, Default, Clone)]
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

    pub fn end(&self) -> Position {
        self.position.after(self)
    }
}
