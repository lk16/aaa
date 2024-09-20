use std::{collections::HashSet, fmt::Display, path::PathBuf};

use crate::{
    common::{formatting::join_display_prefixed, position::Position, traits::HasPosition},
    cross_referencer::types::identifiable::{Identifiable, ReturnTypes, Type},
};

pub enum TypeError {
    BranchError(BranchError),
    CondtionError(ConditionError),
    WhileError(WhileError),
    StackUndeflow(StackUndeflow),
    DoesNotReturn,
    UnreachableCode(UnreachableCode),
    StackError(StackError),
    ParameterCountError(ParameterCountError),
    FunctionTypeError(FunctionTypeError),
    ReturnStackError(ReturnStackError),
    UseStackUnderflow(UseStackUnderflow),
    NameCollision(NameCollision),
    GetFieldStackUnderflow(GetFieldStackUnderflow),
    GetFieldFromNonStruct(GetFieldFromNonStruct),
    GetFieldNotFound(GetFieldNotFound),
    SetFieldStackUnderflow(SetFieldStackUnderflow),
    SetFieldOnNonStruct(SetFieldOnNonStruct),
    SetFieldNotFound(SetFieldNotFound),
    SetFieldTypeError(SetFieldTypeError),
    AssignmentStackSizeError(AssignmentStackSizeError),
    AssignedVariableNotFound(AssignedVariableNotFound),
    AssignmentTypeError(AssignmentTypeError),
    MatchStackUnderflow(MatchStackUnderflow),
    MatchNonEnum(MatchNonEnum),
    MatchUnexpectedEnum(MatchUnexpectedEnum),
    CollidingCaseBlocks(CollidingCaseBlocks),
    CollidingDefaultBlocks(CollidingDefaultBlocks),
    UnhandledEnumVariants(UnhandledEnumVariants),
    UnreachableDefault(UnreachableDefault),
    InconsistentMatchChildren(InconsistentMatchChildren),
    UnexpectedCaseVariableCount(UnexpectedCaseVariableCount),
    MemberFunctionWithoutArguments(MemberFunctionWithoutArguments),
    MemberFunctionInvalidTarget(MemberFunctionInvalidTarget),
    MemberFunctionUnexpectedTarget(MemberFunctionUnexpectedTarget),
    MainFunctionNotFound(MainFunctionNotFound),
    InvalidMainSignature(InvalidMainSignature),
    MainNonFunction(MainNonFunction),
}

impl Display for TypeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::BranchError(error) => write!(f, "{}", error),
            Self::CondtionError(error) => write!(f, "{}", error),
            Self::WhileError(error) => write!(f, "{}", error),
            Self::StackUndeflow(error) => write!(f, "{}", error),
            Self::DoesNotReturn => unreachable!(),
            Self::UnreachableCode(error) => write!(f, "{}", error),
            Self::StackError(error) => write!(f, "{}", error),
            Self::ParameterCountError(error) => write!(f, "{}", error),
            Self::FunctionTypeError(error) => write!(f, "{}", error),
            Self::ReturnStackError(error) => write!(f, "{}", error),
            Self::UseStackUnderflow(error) => write!(f, "{}", error),
            Self::NameCollision(error) => write!(f, "{}", error),
            Self::GetFieldStackUnderflow(error) => write!(f, "{}", error),
            Self::GetFieldFromNonStruct(error) => write!(f, "{}", error),
            Self::GetFieldNotFound(error) => write!(f, "{}", error),
            Self::SetFieldStackUnderflow(error) => write!(f, "{}", error),
            Self::SetFieldOnNonStruct(error) => write!(f, "{}", error),
            Self::SetFieldNotFound(error) => write!(f, "{}", error),
            Self::SetFieldTypeError(error) => write!(f, "{}", error),
            Self::AssignmentStackSizeError(error) => write!(f, "{}", error),
            Self::AssignedVariableNotFound(error) => write!(f, "{}", error),
            Self::AssignmentTypeError(error) => write!(f, "{}", error),
            Self::MatchStackUnderflow(error) => write!(f, "{}", error),
            Self::MatchNonEnum(error) => write!(f, "{}", error),
            Self::MatchUnexpectedEnum(error) => write!(f, "{}", error),
            Self::CollidingCaseBlocks(error) => write!(f, "{}", error),
            Self::CollidingDefaultBlocks(error) => write!(f, "{}", error),
            Self::UnhandledEnumVariants(error) => write!(f, "{}", error),
            Self::UnreachableDefault(error) => write!(f, "{}", error),
            Self::InconsistentMatchChildren(error) => write!(f, "{}", error),
            Self::UnexpectedCaseVariableCount(error) => write!(f, "{}", error),
            Self::MemberFunctionWithoutArguments(error) => write!(f, "{}", error),
            Self::MemberFunctionInvalidTarget(error) => write!(f, "{}", error),
            Self::MemberFunctionUnexpectedTarget(error) => write!(f, "{}", error),
            Self::MainFunctionNotFound(error) => write!(f, "{}", error),
            Self::InvalidMainSignature(error) => write!(f, "{}", error),
            Self::MainNonFunction(error) => write!(f, "{}", error),
        }
    }
}

pub type TypeResult = Result<Vec<Type>, TypeError>;

pub struct BranchError {
    pub position: Position,
    pub before_stack: Vec<Type>,
    pub if_stack: Vec<Type>,
    pub else_stack: Vec<Type>,
}

impl Display for BranchError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Mismatching branch types:", self.position)?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("before stack: ", " ", &self.before_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("    if stack: ", " ", &self.if_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("  else stack: ", " ", &self.else_stack)
        )
    }
}

pub fn branch_error(
    position: Position,
    before_stack: Vec<Type>,
    if_stack: Vec<Type>,
    else_stack: Vec<Type>,
) -> TypeResult {
    Err(TypeError::BranchError(BranchError {
        position,
        before_stack,
        if_stack,
        else_stack,
    }))
}

pub struct ConditionError {
    pub position: Position,
    pub before_stack: Vec<Type>,
    pub after_stack: Vec<Type>,
    pub after_expected_stack: Vec<Type>,
}

impl Display for ConditionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Unexpected stack after condition:", self.position)?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("  before: ", " ", &self.before_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("   after: ", " ", &self.after_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("expected: ", " ", &self.after_expected_stack)
        )
    }
}

pub fn condition_error(
    position: Position,
    before_stack: Vec<Type>,
    after_stack: Vec<Type>,
    after_expected_stack: Vec<Type>,
) -> TypeResult {
    Err(TypeError::CondtionError(ConditionError {
        position,
        before_stack,
        after_stack,
        after_expected_stack,
    }))
}

pub struct WhileError {
    pub position: Position,
    pub before_stack: Vec<Type>,
    pub after_stack: Vec<Type>,
}

impl Display for WhileError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Stack types changed in loop:", self.position)?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("  before: ", " ", &self.before_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("   after: ", " ", &self.after_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("expected: ", " ", &self.before_stack)
        )
    }
}

pub fn while_error(
    position: Position,
    before_stack: Vec<Type>,
    after_stack: Vec<Type>,
) -> TypeResult {
    Err(TypeError::WhileError(WhileError {
        position,
        before_stack,
        after_stack,
    }))
}

pub struct StackUndeflow {
    pub position: Position,
    pub called: String,
    pub before_stack: Vec<Type>,
    pub expected_stack_top: Vec<Type>,
}

impl Display for StackUndeflow {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Stack underflow when calling {}",
            self.position, self.called
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("       stack: ", " ", &self.before_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("expected top: ", " ", &self.expected_stack_top)
        )
    }
}

pub fn stack_underflow(
    position: Position,
    called: String,
    before_stack: Vec<Type>,
    expected_stack_top: Vec<Type>,
) -> TypeResult {
    Err(TypeError::StackUndeflow(StackUndeflow {
        position,
        called,
        before_stack,
        expected_stack_top,
    }))
}

pub fn does_not_return() -> TypeResult {
    Err(TypeError::DoesNotReturn)
}

pub struct UnreachableCode {
    pub position: Position,
}

impl Display for UnreachableCode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Code is unreachable", self.position)
    }
}

pub fn unreachable_code(position: Position) -> TypeResult {
    Err(TypeError::UnreachableCode(UnreachableCode { position }))
}

pub struct StackError {
    pub position: Position,
    pub called: String,
    pub before_stack: Vec<Type>,
    pub expected_stack_top: Vec<Type>,
}

impl Display for StackError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Invalid stack when calling {}",
            self.position, self.called
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("       stack: ", " ", &self.before_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("expected top: ", " ", &self.expected_stack_top)
        )
    }
}

pub fn stack_error(
    position: Position,
    called: String,
    before_stack: Vec<Type>,
    expected_stack_top: Vec<Type>,
) -> TypeResult {
    Err(TypeError::StackError(StackError {
        position,
        called,
        before_stack,
        expected_stack_top,
    }))
}

pub struct ParameterCountError {
    pub position: Position,
    pub found: usize,
    pub expected: usize,
}

impl Display for ParameterCountError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Unexpected number of parameters", self.position)?;
        writeln!(f, "   Found: {}", self.found)?;
        writeln!(f, "Expected: {}", self.expected)
    }
}

pub fn parameter_count_error(position: Position, found: usize, expected: usize) -> TypeResult {
    Err(TypeError::ParameterCountError(ParameterCountError {
        position,
        found,
        expected,
    }))
}

pub struct FunctionTypeError {
    pub position: Position,
    pub func_name: String,
    pub found: ReturnTypes,
    pub expected: ReturnTypes,
}

impl Display for FunctionTypeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Computed stack types don't match signature for function \"{}\"",
            self.position, self.func_name
        )?;
        writeln!(f, "   Found: {}", self.found)?;
        writeln!(f, "Expected: {}", self.expected)
    }
}

pub fn function_type_error<T>(
    position: Position,
    func_name: String,
    found: ReturnTypes,
    expected: ReturnTypes,
) -> Result<T, TypeError> {
    Err(TypeError::FunctionTypeError(FunctionTypeError {
        position,
        func_name,
        found,
        expected,
    }))
}

pub struct ReturnStackError {
    pub position: Position,
    pub found: ReturnTypes,
    pub expected: ReturnTypes,
}

impl Display for ReturnStackError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Invalid stack when using \"return\"", self.position)?;
        writeln!(f, "   Found: {}", self.found)?;
        writeln!(f, "Expected: {}", self.expected)
    }
}

pub fn return_stack_error(
    position: Position,
    found: ReturnTypes,
    expected: ReturnTypes,
) -> TypeResult {
    Err(TypeError::ReturnStackError(ReturnStackError {
        position,
        found,
        expected,
    }))
}

pub struct UseStackUnderflow {
    pub position: Position,
    pub stack: Vec<Type>,
    pub used_var_count: usize,
}

impl Display for UseStackUnderflow {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot use {} value(s), because the stack is too small.",
            self.position, self.used_var_count
        )?;
        writeln!(f, "{}", join_display_prefixed("Stack: ", " ", &self.stack))
    }
}

pub fn use_stack_underflow(
    position: Position,
    stack: Vec<Type>,
    used_var_count: usize,
) -> TypeResult {
    Err(TypeError::UseStackUnderflow(UseStackUnderflow {
        position,
        stack,
        used_var_count,
    }))
}

pub trait NameCollisionItem: HasPosition + Display {}

impl<T: HasPosition + Display> NameCollisionItem for T {}

pub struct NameCollision {
    pub items: [Box<dyn NameCollisionItem>; 2],
}

impl Display for NameCollision {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "Found name collision:")?;

        let mut outputs: Vec<_> = self
            .items
            .iter()
            .map(|item| (item.position(), format!("{}: {}", item.position(), item)))
            .collect();

        outputs.sort_by_key(|(position, _)| position.clone());

        for (_, output) in outputs {
            writeln!(f, "{}", output)?;
        }

        Ok(())
    }
}

pub fn name_collision<T>(
    first: Box<dyn NameCollisionItem>,
    second: Box<dyn NameCollisionItem>,
) -> Result<T, TypeError> {
    Err(TypeError::NameCollision(NameCollision {
        items: [first, second],
    }))
}

pub struct GetFieldStackUnderflow {
    pub position: Position,
    pub field_name: String,
}

impl Display for GetFieldStackUnderflow {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot get field {}, because the stack is empty",
            self.position, self.field_name,
        )
    }
}

pub fn get_field_stack_underflow(position: Position, field_name: String) -> TypeResult {
    Err(TypeError::GetFieldStackUnderflow(GetFieldStackUnderflow {
        position,
        field_name,
    }))
}

pub struct GetFieldFromNonStruct {
    pub position: Position,
    pub field_name: String,
    pub target: Type,
}

impl Display for GetFieldFromNonStruct {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Can only get field {} from a struct, found {} {}",
            self.position,
            self.field_name,
            self.target.kind(),
            self.target
        )
    }
}

pub fn get_field_from_non_struct(
    position: Position,
    field_name: String,
    target: Type,
) -> TypeResult {
    Err(TypeError::GetFieldFromNonStruct(GetFieldFromNonStruct {
        position,
        field_name,
        target,
    }))
}

pub struct GetFieldNotFound {
    pub position: Position,
    pub field_name: String,
    pub struct_name: String,
}

impl Display for GetFieldNotFound {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot get field {} from struct {}, because it doesn't exist",
            self.position, self.field_name, self.struct_name
        )
    }
}

pub fn get_field_not_found(
    position: Position,
    field_name: String,
    struct_name: String,
) -> TypeResult {
    Err(TypeError::GetFieldNotFound(GetFieldNotFound {
        position,
        field_name,
        struct_name,
    }))
}

pub struct SetFieldStackUnderflow {
    pub position: Position,
    pub field_name: String,
}

impl Display for SetFieldStackUnderflow {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot set field {}, because the stack is empty",
            self.position, self.field_name,
        )
    }
}

pub fn set_field_stack_underflow(position: Position, field_name: String) -> TypeResult {
    Err(TypeError::SetFieldStackUnderflow(SetFieldStackUnderflow {
        position,
        field_name,
    }))
}

pub struct SetFieldOnNonStruct {
    pub position: Position,
    pub field_name: String,
    pub target: Type,
}

impl Display for SetFieldOnNonStruct {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Can only set field {} on a struct, found {} {}",
            self.position,
            self.field_name,
            self.target.kind(),
            self.target
        )
    }
}

pub fn set_field_on_non_struct(position: Position, field_name: String, target: Type) -> TypeResult {
    Err(TypeError::SetFieldOnNonStruct(SetFieldOnNonStruct {
        position,
        field_name,
        target,
    }))
}

pub struct SetFieldNotFound {
    pub position: Position,
    pub field_name: String,
    pub struct_name: String,
}

impl Display for SetFieldNotFound {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot set field {} on struct {}, because it doesn't exist",
            self.position, self.field_name, self.struct_name
        )
    }
}

pub fn set_field_not_found(
    position: Position,
    field_name: String,
    struct_name: String,
) -> TypeResult {
    Err(TypeError::SetFieldNotFound(SetFieldNotFound {
        position,
        field_name,
        struct_name,
    }))
}

pub struct SetFieldTypeError {
    pub position: Position,
    pub field_name: String,
    pub struct_name: String,
    pub expected_stack: Vec<Type>,
    pub found_stack: Vec<Type>,
}

impl Display for SetFieldTypeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Invalid stack types when setting field {} on struct {}:",
            self.position, self.field_name, self.struct_name
        )?;

        writeln!(
            f,
            "{}",
            join_display_prefixed("   Found: ", " ", &self.found_stack)
        )?;
        writeln!(
            f,
            "{}",
            join_display_prefixed("Expected: ", " ", &self.expected_stack)
        )
    }
}

pub fn set_field_type_error(
    position: Position,
    field_name: String,
    struct_name: String,
    expected_stack: Vec<Type>,
    found_stack: Vec<Type>,
) -> TypeResult {
    Err(TypeError::SetFieldTypeError(SetFieldTypeError {
        position,
        field_name,
        struct_name,
        expected_stack,
        found_stack,
    }))
}

pub struct AssignmentStackSizeError {
    pub position: Position,
    pub expected_stack_size: usize,
    pub found_stack_size: usize,
}

impl Display for AssignmentStackSizeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot assign {} value(s) to {} variable(s)",
            self.position, self.found_stack_size, self.expected_stack_size
        )
    }
}

pub fn assignment_stack_size_error(
    position: Position,
    expected_stack_size: usize,
    found_stack_size: usize,
) -> TypeResult {
    Err(TypeError::AssignmentStackSizeError(
        AssignmentStackSizeError {
            position,
            expected_stack_size,
            found_stack_size,
        },
    ))
}

pub struct AssignedVariableNotFound {
    pub position: Position,
    pub variable_name: String,
}

impl Display for AssignedVariableNotFound {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot set variable {}, because it doesn't exist.",
            self.position, self.variable_name
        )
    }
}

pub fn assigned_variable_not_found(position: Position, variable_name: String) -> TypeResult {
    Err(TypeError::AssignedVariableNotFound(
        AssignedVariableNotFound {
            position,
            variable_name,
        },
    ))
}

pub struct AssignmentTypeError {
    pub position: Position,
    pub field_name: String,
    pub expected_type: Type,
    pub found_type: Type,
}

impl Display for AssignmentTypeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot set variable {}, due to invalid type.",
            self.position, self.field_name
        )?;
        writeln!(f, "Expected: {}", self.expected_type)?;
        writeln!(f, "   Found: {}", self.found_type)
    }
}

pub fn assignment_type_error(
    position: Position,
    field_name: String,
    expected_type: Type,
    found_type: Type,
) -> TypeResult {
    Err(TypeError::AssignmentTypeError(AssignmentTypeError {
        position,
        field_name,
        expected_type,
        found_type,
    }))
}

pub struct MatchStackUnderflow {
    pub position: Position,
}

impl Display for MatchStackUnderflow {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Cannot match on an empty stack", self.position)
    }
}

pub fn match_stack_underflow(position: Position) -> TypeResult {
    Err(TypeError::MatchStackUnderflow(MatchStackUnderflow {
        position,
    }))
}

pub struct MatchNonEnum {
    pub position: Position,
    pub type_: Type,
}

impl Display for MatchNonEnum {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Cannot match on {} {}",
            self.position,
            self.type_.kind(),
            self.type_
        )
    }
}

pub fn match_non_enum(position: Position, type_: Type) -> TypeResult {
    Err(TypeError::MatchNonEnum(MatchNonEnum { position, type_ }))
}

pub struct MatchUnexpectedEnum {
    pub position: Position,
    pub expected_enum_name: String,
    pub found_enum_name: String,
}

impl Display for MatchUnexpectedEnum {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Unexpected enum case:", self.position)?;
        writeln!(f, "Expected: {}", self.expected_enum_name)?;
        writeln!(f, "   Found: {}", self.found_enum_name)
    }
}

pub fn match_unexpected_enum<T>(
    position: Position,
    expected_enum_name: String,
    found_enum_name: String,
) -> Result<T, TypeError> {
    Err(TypeError::MatchUnexpectedEnum(MatchUnexpectedEnum {
        position,
        expected_enum_name,
        found_enum_name,
    }))
}

pub struct CollidingCaseBlocks {
    pub enum_name: String,
    pub variant_name: String,
    pub positions: [Position; 2],
}

impl Display for CollidingCaseBlocks {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "Found colliding case blocks:")?;

        for position in &self.positions {
            writeln!(
                f,
                "{}: case {}:{}",
                position, self.enum_name, self.variant_name
            )?;
        }

        Ok(())
    }
}

pub fn colliding_case_blocks<T>(
    enum_name: String,
    variant_name: String,
    positions: [Position; 2],
) -> Result<T, TypeError> {
    Err(TypeError::CollidingCaseBlocks(CollidingCaseBlocks {
        enum_name,
        variant_name,
        positions,
    }))
}

pub struct CollidingDefaultBlocks {
    pub positions: [Position; 2],
}

impl Display for CollidingDefaultBlocks {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "Found colliding default blocks:")?;

        for position in &self.positions {
            writeln!(f, "{}: default", position)?;
        }

        Ok(())
    }
}

pub fn colliding_default_blocks<T>(positions: [Position; 2]) -> Result<T, TypeError> {
    Err(TypeError::CollidingDefaultBlocks(CollidingDefaultBlocks {
        positions,
    }))
}

pub struct UnhandledEnumVariants {
    pub position: Position,
    pub enum_name: String,
    pub variant_names: HashSet<String>,
}

impl Display for UnhandledEnumVariants {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Some enum variant(s) are unhandled:", self.position)?;

        for variant_name in &self.variant_names {
            writeln!(f, "case {}:{}", self.enum_name, variant_name)?;
        }

        Ok(())
    }
}

pub fn unhandled_enum_variants<T>(
    position: Position,
    enum_name: String,
    variant_names: HashSet<String>,
) -> Result<T, TypeError> {
    Err(TypeError::UnhandledEnumVariants(UnhandledEnumVariants {
        position,
        enum_name,
        variant_names,
    }))
}

pub struct UnreachableDefault {
    pub position: Position,
}

impl Display for UnreachableDefault {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: Default block is unreachable", self.position)
    }
}

pub fn unreachable_default<T>(position: Position) -> Result<T, TypeError> {
    Err(TypeError::UnreachableDefault(UnreachableDefault {
        position,
    }))
}

pub struct InconsistentMatchChildren {
    pub position: Position,
    pub child_return_types: Vec<(String, Position, ReturnTypes)>,
}

impl Display for InconsistentMatchChildren {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Children of match have inconsistent stacks:",
            self.position
        )?;

        for (name, _, child_return_type) in &self.child_return_types {
            writeln!(f, "{}: {}", name, child_return_type)?;
        }

        Ok(())
    }
}

pub fn inconsistent_match_children<T>(
    position: Position,
    child_return_types: Vec<(String, Position, ReturnTypes)>,
) -> Result<T, TypeError> {
    Err(TypeError::InconsistentMatchChildren(
        InconsistentMatchChildren {
            position,
            child_return_types,
        },
    ))
}

pub struct UnexpectedCaseVariableCount {
    pub position: Position,
    pub enum_name: String,
    pub variant_name: String,
    pub expected_count: usize,
    pub found_count: usize,
}

impl Display for UnexpectedCaseVariableCount {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Unexpected amount of variables for case {}:{}:",
            self.position, self.enum_name, self.variant_name,
        )?;

        if self.expected_count == 0 {
            writeln!(f, "Expected: {}", self.expected_count)?;
        } else {
            writeln!(f, "Expected: 0 or {}", self.expected_count)?;
        }

        writeln!(f, "   Found: {}", self.found_count)
    }
}

pub fn unexpected_case_variable_count<T>(
    position: Position,
    enum_name: String,
    variant_name: String,
    expected_count: usize,
    found_count: usize,
) -> Result<T, TypeError> {
    Err(TypeError::UnexpectedCaseVariableCount(
        UnexpectedCaseVariableCount {
            position,
            enum_name,
            variant_name,
            expected_count,
            found_count,
        },
    ))
}

pub struct MemberFunctionWithoutArguments {
    pub position: Position,
    pub function_name: String,
}

impl Display for MemberFunctionWithoutArguments {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Member function {} should have associated type as first argument",
            self.position, self.function_name
        )
    }
}

pub fn member_function_without_arguments<T>(
    position: Position,
    function_name: String,
) -> Result<T, TypeError> {
    Err(TypeError::MemberFunctionWithoutArguments(
        MemberFunctionWithoutArguments {
            position,
            function_name,
        },
    ))
}

pub struct MemberFunctionInvalidTarget {
    pub position: Position,
    pub function_name: String,
    pub target: Type,
}

impl Display for MemberFunctionInvalidTarget {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Invalid first argument of member function {}",
            self.position, self.function_name
        )?;

        writeln!(f, "Expected: struct or enum")?;
        writeln!(f, "   Found: {}", self.target)
    }
}

pub fn member_function_invalid_target<T>(
    position: Position,
    function_name: String,
    target: Type,
) -> Result<T, TypeError> {
    Err(TypeError::MemberFunctionInvalidTarget(
        MemberFunctionInvalidTarget {
            position,
            function_name,
            target,
        },
    ))
}

pub struct MemberFunctionUnexpectedTarget {
    pub position: Position,
    pub function_name: String,
    pub expected_target_name: String,
    pub found_target_name: String,
}

impl Display for MemberFunctionUnexpectedTarget {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: First argument of member function {} has unexpected type",
            self.position, self.function_name
        )?;

        writeln!(f, "Expected: {}", self.expected_target_name)?;
        writeln!(f, "   Found: {}", self.found_target_name)
    }
}

pub fn member_function_unexpected_target<T>(
    position: Position,
    function_name: String,
    expected_target_name: String,
    found_target_name: String,
) -> Result<T, TypeError> {
    Err(TypeError::MemberFunctionUnexpectedTarget(
        MemberFunctionUnexpectedTarget {
            position,
            function_name,
            expected_target_name,
            found_target_name,
        },
    ))
}

pub struct MainFunctionNotFound {
    pub main_file: PathBuf,
}

impl Display for MainFunctionNotFound {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}: No main function found", self.main_file.display())
    }
}

pub fn main_function_not_found<T>(main_file: PathBuf) -> Result<T, TypeError> {
    Err(TypeError::MainFunctionNotFound(MainFunctionNotFound {
        main_file,
    }))
}

pub struct InvalidMainSignature {
    pub position: Position,
}

impl Display for InvalidMainSignature {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: Main function has wrong signature, it should have:",
            self.position
        )?;
        writeln!(f, "- no type parameters")?;
        writeln!(f, "- either no arguments or one vec[str] argument")?;
        writeln!(f, "- return either nothing or an int")
    }
}

pub fn invalid_main_signature<T>(position: Position) -> Result<T, TypeError> {
    Err(TypeError::InvalidMainSignature(InvalidMainSignature {
        position,
    }))
}

pub struct MainNonFunction {
    pub position: Position,
    pub identifiable: Identifiable,
}

impl Display for MainNonFunction {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "{}: main should be a function, found {} instead.",
            self.position, self.identifiable
        )
    }
}

pub fn main_non_function<T>(
    position: Position,
    identifiable: Identifiable,
) -> Result<T, TypeError> {
    Err(TypeError::MainNonFunction(MainNonFunction {
        position,
        identifiable,
    }))
}
