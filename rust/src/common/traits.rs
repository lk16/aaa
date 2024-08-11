use super::position::Position;

pub trait HasPosition {
    fn position(&self) -> Position;
}
