#![allow(dead_code)] // TODO

use std::{fmt::Debug, path::PathBuf};

use crate::common::position::Position;

use super::types::Identifiable;

pub struct UnknownIdentifiable {
    pub position: Position,
    pub name: String,
}

impl Debug for UnknownIdentifiable {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: Unknown identifiable {}", self.position, self.name)
    }
}

pub struct CyclicDependency {
    pub dependencies: Vec<PathBuf>,
}

pub struct UnexpectedBuiltin {
    pub position: Position,
    pub identifiable: Identifiable,
}

pub struct CollidingIdentifiables {
    pub identifiables: [Identifiable; 2],
}

impl CollidingIdentifiables {
    pub fn first(&self) -> Identifiable {
        self.identifiables
            .iter()
            .min_by_key(|i| i.position())
            .unwrap()
            .clone()
    }

    pub fn second(&self) -> Identifiable {
        self.identifiables
            .iter()
            .max_by_key(|i| i.position())
            .unwrap()
            .clone()
    }
}

pub struct ImportNotFound {
    pub position: Position,
}

impl Debug for ImportNotFound {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: Cannot find imported item.", self.position)
    }
}

pub struct IndirectImport {
    pub position: Position,
}

impl Debug for IndirectImport {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: Indirect imports are forbidden.", self.position)
    }
}

pub struct InvalidArgument {
    pub position: Position,
    pub identifiable: Identifiable,
}

pub struct UnexpectedParameterCount {
    pub position: Position,
    pub type_name: String,
    pub expected_count: usize,
    pub found_count: usize,
}

pub struct InvalidReturnType {
    pub position: Position,
    pub identifiable: Identifiable,
}

impl Debug for UnexpectedParameterCount {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}: Unexpected parameter count for type {}\n",
            self.position, self.type_name
        )?;
        write!(f, "Expected: {}\n", self.expected_count)?;
        write!(f, "Found:    {}\n", self.found_count)
    }
}

pub enum CrossReferencerError {
    CollidingIdentifiables(CollidingIdentifiables),
    CyclicDependency(CyclicDependency),
    ImportNotFound(ImportNotFound),
    IndirectImport(IndirectImport),
    InvalidArgument(InvalidArgument),
    InvalidReturnType(InvalidReturnType),
    UnexpectedBuiltin(UnexpectedBuiltin),
    UnknownIdentifiable(UnknownIdentifiable),
}

// TODO replace From<...> implementations by macro

impl From<CyclicDependency> for CrossReferencerError {
    fn from(value: CyclicDependency) -> Self {
        Self::CyclicDependency(value)
    }
}

impl From<UnexpectedBuiltin> for CrossReferencerError {
    fn from(value: UnexpectedBuiltin) -> Self {
        Self::UnexpectedBuiltin(value)
    }
}

impl From<CollidingIdentifiables> for CrossReferencerError {
    fn from(value: CollidingIdentifiables) -> Self {
        Self::CollidingIdentifiables(value)
    }
}

impl From<ImportNotFound> for CrossReferencerError {
    fn from(value: ImportNotFound) -> Self {
        Self::ImportNotFound(value)
    }
}

impl From<IndirectImport> for CrossReferencerError {
    fn from(value: IndirectImport) -> Self {
        Self::IndirectImport(value)
    }
}

impl From<InvalidArgument> for CrossReferencerError {
    fn from(value: InvalidArgument) -> Self {
        Self::InvalidArgument(value)
    }
}

impl From<UnknownIdentifiable> for CrossReferencerError {
    fn from(value: UnknownIdentifiable) -> Self {
        Self::UnknownIdentifiable(value)
    }
}

impl From<InvalidReturnType> for CrossReferencerError {
    fn from(value: InvalidReturnType) -> Self {
        Self::InvalidReturnType(value)
    }
}

impl Debug for CrossReferencerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::CollidingIdentifiables(_) => write!(f, "{}", "CollidingIdentifiables"), // TODO
            Self::CyclicDependency(_) => write!(f, "{}", "CyclicDependency"),             // TODO
            Self::ImportNotFound(error) => write!(f, "{:?}", error),
            Self::IndirectImport(error) => write!(f, "{:?}", error),
            Self::InvalidArgument(_) => write!(f, "{}", "InvalidArgument"), // TODO
            Self::InvalidReturnType(_) => write!(f, "{}", "InvalidReturnType"), // TODO
            Self::UnexpectedBuiltin(_) => write!(f, "{}", "UnexpectedBuiltin"), // TODO
            Self::UnknownIdentifiable(error) => write!(f, "{:?}", error),
        }
    }
}

// TODO check all Debug outputs
