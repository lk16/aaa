use std::{fmt::Display, path::PathBuf};

use crate::{
    common::position::Position,
    type_checker::errors::{NameCollision, NameCollisionItem},
};

use super::types::identifiable::Identifiable;

pub enum CrossReferencerError {
    CyclicDependency(CyclicDependency),
    ImportNotFound(ImportNotFound),
    IndirectImport(IndirectImport),
    UnexpectedBuiltin(UnexpectedBuiltin),
    UnknownIdentifiable(UnknownIdentifiable),
    NameCollision(NameCollision),
    GetFunctionNotFound(GetFunctionNotFound),
    GetFunctionNonFunction(GetFunctionNonFunction),
}

impl Display for CrossReferencerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::CyclicDependency(error) => write!(f, "{}", error),
            Self::ImportNotFound(error) => write!(f, "{}", error),
            Self::IndirectImport(error) => write!(f, "{}", error),
            Self::UnexpectedBuiltin(error) => write!(f, "{}", error),
            Self::UnknownIdentifiable(error) => write!(f, "{}", error),
            Self::NameCollision(error) => write!(f, "{}", error),
            Self::GetFunctionNotFound(error) => write!(f, "{}", error),
            Self::GetFunctionNonFunction(error) => write!(f, "{}", error),
        }
    }
}

pub struct UnknownIdentifiable {
    pub position: Position,
    pub name: String,
}

impl Display for UnknownIdentifiable {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Unknown identifiable {}", self.position, self.name)
    }
}

pub fn unknown_identifiable<T>(
    position: Position,
    name: String,
) -> Result<T, CrossReferencerError> {
    Err(CrossReferencerError::UnknownIdentifiable(
        UnknownIdentifiable { position, name },
    ))
}

pub struct CyclicDependency {
    pub dependencies: Vec<PathBuf>,
}

impl Display for CyclicDependency {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "Found cyclic import:")?;

        for dependency in &self.dependencies {
            writeln!(f, "{}", dependency.display())?;
        }

        Ok(())
    }
}

pub fn cyclic_dependency<T>(dependencies: Vec<PathBuf>) -> Result<T, CrossReferencerError> {
    Err(CrossReferencerError::CyclicDependency(CyclicDependency {
        dependencies,
    }))
}

pub struct UnexpectedBuiltin {
    pub position: Position,
    pub identifiable: Identifiable,
}

impl Display for UnexpectedBuiltin {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Found unexpected builtin {}",
            self.position, self.identifiable
        )
    }
}

pub fn unexpected_builtin(position: Position, identifiable: Identifiable) -> CrossReferencerError {
    CrossReferencerError::UnexpectedBuiltin(UnexpectedBuiltin {
        position,
        identifiable,
    })
}

pub struct ImportNotFound {
    pub position: Position,
    pub name: String,
    pub target_file: PathBuf,
}

impl Display for ImportNotFound {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot find {} in {}.",
            self.position,
            self.name,
            self.target_file.display(),
        )
    }
}

pub fn import_not_found<T>(
    position: Position,
    name: String,
    target_file: PathBuf,
) -> Result<T, CrossReferencerError> {
    Err(CrossReferencerError::ImportNotFound(ImportNotFound {
        position,
        name,
        target_file,
    }))
}

pub struct IndirectImport {
    pub position: Position,
}

impl Display for IndirectImport {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Indirect imports are forbidden.", self.position)
    }
}

pub fn indirect_import<T>(position: Position) -> Result<T, CrossReferencerError> {
    Err(CrossReferencerError::IndirectImport(IndirectImport {
        position,
    }))
}

pub fn name_collision<T>(
    first: Box<dyn NameCollisionItem>,
    second: Box<dyn NameCollisionItem>,
) -> Result<T, CrossReferencerError> {
    Err(CrossReferencerError::NameCollision(NameCollision {
        items: [first, second],
    }))
}

pub struct GetFunctionNotFound {
    pub position: Position,
    pub function_name: String,
}

impl Display for GetFunctionNotFound {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot get function {}, it does not exist.",
            self.position, self.function_name
        )
    }
}

pub fn get_function_not_found<T>(
    position: Position,
    function_name: String,
) -> Result<T, CrossReferencerError> {
    Err(CrossReferencerError::GetFunctionNotFound(
        GetFunctionNotFound {
            position,
            function_name,
        },
    ))
}

pub struct GetFunctionNonFunction {
    pub position: Position,
    pub function_name: String,
    pub identifiable: Identifiable,
}

impl Display for GetFunctionNonFunction {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot get function {}, found {} instead.",
            self.position, self.function_name, self.identifiable
        )
    }
}

pub fn get_function_non_function<T>(
    position: Position,
    function_name: String,
    identifiable: Identifiable,
) -> Result<T, CrossReferencerError> {
    Err(CrossReferencerError::GetFunctionNonFunction(
        GetFunctionNonFunction {
            position,
            function_name,
            identifiable,
        },
    ))
}
