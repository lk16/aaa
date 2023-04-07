// TODO remove
#![allow(dead_code)]
#![allow(unused_variables)]
#![allow(unreachable_code)]

use std::{
    cell::RefCell,
    env,
    fmt::{Debug, Formatter, Result},
    fs,
    hash::Hash,
    path::Path,
    process,
    rc::Rc,
    time::{SystemTime, UNIX_EPOCH},
    vec,
};

use crate::{
    map::{Map, MapIterator},
    set::{Set, SetIterator},
    vector::VectorIterator,
};
use crate::{var::Variable, vector::Vector};

#[derive(Clone, PartialEq, Eq, Hash)]
pub enum VariableEnum<T>
// TODO give better name
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    Builtin(Variable<T>),
    Custom(T),
}

impl<T> Debug for VariableEnum<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::Builtin(b) => write!(f, "{b:?}"),
            Self::Custom(c) => write!(f, "{c:?}"),
        }
    }
}

pub struct Stack<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    items: Vec<VariableEnum<T>>,
}

impl<T> Debug for Stack<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "Stack ({}):", self.len())?;
        for item in self.items.iter() {
            write!(f, " ")?;
            write!(f, "{:?}", item)?;
        }
        Ok(())
    }
}

impl<T> Stack<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    pub fn new() -> Self {
        Self { items: Vec::new() }
    }

    pub fn push(&mut self, v: VariableEnum<T>) {
        self.items.push(v);
    }

    fn push_builtin(&mut self, v: Variable<T>) {
        self.push(VariableEnum::Builtin(v));
    }

    fn push_custom(&mut self, v: T) {
        self.push(VariableEnum::Custom(v));
    }

    fn len(&self) -> usize {
        self.items.len()
    }

    pub fn push_int(&mut self, v: isize) {
        let item = Variable::Integer(v);
        self.push_builtin(item);
    }

    pub fn push_bool(&mut self, v: bool) {
        let item = Variable::Boolean(v);
        self.push_builtin(item);
    }

    pub fn push_str(&mut self, v: String) {
        let item = Variable::String(Rc::new(RefCell::new(v)));
        self.push_builtin(item);
    }

    pub fn push_vector(&mut self, v: Vector<VariableEnum<T>>) {
        let item = Variable::Vector(Rc::new(RefCell::new(v)));
        self.push_builtin(item);
    }

    pub fn push_set(&mut self, v: Set<VariableEnum<T>>) {
        let item = Variable::Set(Rc::new(RefCell::new(v)));
        self.push_builtin(item);
    }

    pub fn push_map(&mut self, v: Map<VariableEnum<T>, VariableEnum<T>>) {
        let item = Variable::Map(Rc::new(RefCell::new(v)));
        self.push_builtin(item);
    }

    pub fn push_vector_iter(&mut self, v: VectorIterator<VariableEnum<T>>) {
        let item = Variable::VectorIterator(Rc::new(RefCell::new(v)));
        self.push_builtin(item);
    }

    pub fn push_map_iter(&mut self, v: MapIterator<VariableEnum<T>, VariableEnum<T>>) {
        let item = Variable::MapIterator(Rc::new(RefCell::new(v)));
        self.push_builtin(item);
    }

    pub fn push_set_iter(&mut self, v: SetIterator<VariableEnum<T>>) {
        let item = Variable::SetIterator(Rc::new(RefCell::new(v)));
        self.push_builtin(item);
    }

    pub fn push_none(&mut self) {
        self.push_builtin(Variable::None);
    }

    pub fn pop(&mut self) -> VariableEnum<T> {
        match self.items.pop() {
            Some(popped) => popped,
            None => todo!(), // TODO handle popping from empty stack
        }
    }

    fn pop_builtin(&mut self) -> Variable<T> {
        match self.pop() {
            VariableEnum::Builtin(popped) => popped,
            VariableEnum::Custom(_) => todo!(), // Type error
        }
    }

    fn pop_custom(&mut self) -> T {
        match self.pop() {
            VariableEnum::Builtin(_) => todo!(), // Type error
            VariableEnum::Custom(popped) => popped,
        }
    }

    fn top(&mut self) -> &VariableEnum<T> {
        match self.items.last() {
            None => todo!(),
            Some(v) => v,
        }
    }

    pub fn pop_int(&mut self) -> isize {
        match self.pop_builtin() {
            Variable::Integer(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_bool(&mut self) -> bool {
        match self.pop_builtin() {
            Variable::Boolean(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_str(&mut self) -> Rc<RefCell<String>> {
        match self.pop_builtin() {
            Variable::String(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_vector(&mut self) -> Rc<RefCell<Vector<VariableEnum<T>>>> {
        match self.pop_builtin() {
            Variable::Vector(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_set(&mut self) -> Rc<RefCell<Set<VariableEnum<T>>>> {
        match self.pop_builtin() {
            Variable::Set(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_map(&mut self) -> Rc<RefCell<Map<VariableEnum<T>, VariableEnum<T>>>> {
        match self.pop_builtin() {
            Variable::Map(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_vector_iterator(&mut self) -> Rc<RefCell<VectorIterator<VariableEnum<T>>>> {
        match self.pop_builtin() {
            Variable::VectorIterator(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_map_iterator(
        &mut self,
    ) -> Rc<RefCell<MapIterator<VariableEnum<T>, VariableEnum<T>>>> {
        match self.pop_builtin() {
            Variable::MapIterator(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_set_iterator(&mut self) -> Rc<RefCell<SetIterator<VariableEnum<T>>>> {
        match self.pop_builtin() {
            Variable::SetIterator(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn print(&mut self) {
        let top = self.pop();
        print!("{top:?}");
    }

    pub fn dup(&mut self) {
        let len = self.len();

        if len < 1 {
            panic!("Stack underflow!\n");
        }

        self.push(self.items[len - 1].clone());
    }

    pub fn swap(&mut self) {
        let len = self.len();

        if len < 2 {
            panic!("Stack underflow!\n");
        }

        self.items.swap(len - 1, len - 2);
    }

    pub fn assert(&mut self) {
        if !self.pop_bool() {
            eprintln!("Assertion failure!");
            process::exit(1);
        }
    }

    pub fn over(&mut self) {
        let len = self.len();

        if len < 2 {
            panic!("Stack underflow!\n");
        }

        self.push(self.items[len - 2].clone());
    }

    pub fn rot(&mut self) {
        let len = self.len();

        if len < 3 {
            panic!("Stack underflow!\n");
        }

        self.items.swap(len - 3, len - 2);
        self.items.swap(len - 2, len - 1);
    }

    pub fn plus(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_int(lhs + rhs);
    }

    pub fn minus(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_int(lhs - rhs);
    }

    pub fn multiply(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_int(lhs * rhs);
    }

    pub fn divide(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();

        if rhs == 0 {
            self.push_int(0);
            self.push_bool(false);
        } else {
            self.push_int(lhs / rhs);
            self.push_bool(true);
        }
    }

    pub fn modulo(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();

        if rhs == 0 {
            self.push_int(0);
            self.push_bool(false);
        } else {
            self.push_int(lhs % rhs);
            self.push_bool(true);
        }
    }

    pub fn repr(&mut self) {
        let top = self.pop();
        let repr = format!("{top:?}");
        self.push_str(repr);
    }

    pub fn drop(&mut self) {
        self.pop();
    }

    pub fn less(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_bool(lhs < rhs);
    }

    pub fn less_equal(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_bool(lhs <= rhs);
    }

    pub fn unequal(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_bool(lhs != rhs);
    }

    pub fn greater(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_bool(lhs > rhs);
    }

    pub fn greater_equal(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_bool(lhs >= rhs);
    }

    pub fn equals(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();
        self.push_bool(lhs == rhs);
    }

    pub fn or(&mut self) {
        let rhs = self.pop_bool();
        let lhs = self.pop_bool();
        self.push_bool(lhs || rhs);
    }

    pub fn and(&mut self) {
        let rhs = self.pop_bool();
        let lhs = self.pop_bool();
        self.push_bool(lhs && rhs);
    }

    pub fn not(&mut self) {
        let value = self.pop_bool();
        self.push_bool(!value);
    }

    pub fn socket(&mut self) {
        todo!(); // Split this into UDP and TCP sockets
                 // See also https://doc.rust-lang.org/std/net/
    }

    pub fn exit(&mut self) -> ! {
        let code = self.pop_int();
        process::exit(code as i32);
    }

    pub fn write(&mut self) {
        todo!(); // Split for actual files on a filesystem and sockets
                 // or consider using the nix library
    }

    pub fn connect(&mut self) {
        todo!();
    }

    pub fn read(&mut self) {
        todo!();
    }

    pub fn bind(&mut self) {
        todo!();
    }

    pub fn listen(&mut self) {
        todo!();
    }

    pub fn accept(&mut self) {
        todo!();
    }

    pub fn nop(&mut self) {}

    pub fn vec_push(&mut self) {
        let pushed = self.pop();
        let vector = self.pop_vector();
        vector.borrow_mut().push(pushed);
    }

    pub fn vec_pop(&mut self) {
        let vector = self.pop_vector();
        let popped = vector.borrow_mut().pop();

        match popped {
            Some(popped) => self.push(popped),
            None => todo!(),
        }
    }

    pub fn vec_get(&mut self) {
        todo!() // This will be removed, renane vec_get_copy() to vec_get()
    }

    pub fn vec_get_copy(&mut self) {
        let offset = self.pop_int();

        let vector_rc = self.pop_vector();
        let vector = (*vector_rc).borrow();

        let gotten = vector.get(offset as usize);
        self.push(gotten);
    }

    pub fn vec_set(&mut self) {
        let value = self.pop();
        let offset = self.pop_int();
        let vector = self.pop_vector();

        vector.borrow_mut().set(offset as usize, value);
    }

    pub fn vec_size(&mut self) {
        let size = (*(self.pop_vector())).borrow().len();
        self.push_int(size as isize);
    }

    pub fn vec_empty(&mut self) {
        let is_empty = (*(self.pop_vector())).borrow().is_empty();
        self.push_bool(is_empty);
    }

    pub fn vec_clear(&mut self) {
        self.pop_vector().borrow_mut().clear();
    }

    pub fn push_map_empty(&mut self) {
        self.push_map(Map::new())
    }

    pub fn map_set(&mut self) {
        let value = self.pop();
        let key = self.pop();
        let map_rc = self.pop_map();
        let mut map = map_rc.borrow_mut();

        (*map).insert(key, value);
    }

    pub fn map_get(&mut self) {
        todo!(); // this will be removed, rename map_get_copy() to map_get(), similar to vec_get_copy()
    }

    pub fn map_get_copy(&mut self) {
        let key = self.pop();
        let map_rc = self.pop_map();
        let map = map_rc.borrow_mut();

        match map.get(&key) {
            None => todo!(), // In C we would push NULL here. Figure out what to do.
            Some(value) => {
                self.push(value.clone());
                self.push_bool(true);
            }
        }
    }

    pub fn map_has_key(&mut self) {
        let key = self.pop();

        let map_rc = self.pop_map();
        let map = (*map_rc).borrow();

        let has_key = map.contains_key(&key);
        self.push_bool(has_key);
    }

    pub fn map_size(&mut self) {
        let size = (*(self.pop_map())).borrow().len();
        self.push_int(size as isize);
    }

    pub fn map_empty(&mut self) {
        let is_empty = (*(self.pop_map())).borrow().is_empty();
        self.push_bool(is_empty);
    }

    pub fn map_clear(&mut self) {
        self.pop_map().borrow_mut().clear();
    }

    pub fn map_pop(&mut self) {
        let key = self.pop();
        let map_rc = self.pop_map();
        let mut map = map_rc.borrow_mut();

        match map.remove_entry(&key) {
            None => todo!(), // In C we push NULL here, see also map_get_copy()
            Some((k, v)) => self.push(v),
        }
    }

    pub fn map_drop(&mut self) {
        let key = self.pop();
        let map_rc = self.pop_map();
        let mut map = map_rc.borrow_mut();

        match map.remove_entry(&key) {
            None => todo!(), // In C we push NULL here, see also map_get_copy()
            Some(_) => (),
        }
    }

    pub fn str_append(&mut self) {
        // TODO we crash if lhs and rhs are referring the same String
        let lhs_rc = self.pop_str();
        let lhs = (*lhs_rc).borrow();

        let rhs_rc = self.pop_str();
        let rhs = (*rhs_rc).borrow();

        let combined = lhs.clone() + &rhs;
        self.push_str(combined);
    }

    pub fn str_contains(&mut self) {
        let search_rc = self.pop_str();
        let search = (*search_rc).borrow();

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let found = string.contains(&*search);
        self.push_bool(found);
    }

    pub fn str_equals(&mut self) {
        let lhs_rc = self.pop_str();
        let lhs = (*lhs_rc).borrow();

        let rhs_rc = self.pop_str();
        let rhs = (*rhs_rc).borrow();

        self.push_bool(lhs.as_str() == rhs.as_str());
    }

    pub fn str_join(&mut self) {
        let vector_rc = self.pop_vector();
        let vector = vector_rc.borrow();

        let mut parts = vec![];
        for part in vector.iter() {
            match part {
                VariableEnum::Builtin(Variable::String(part)) => {
                    let part = (*part).borrow().clone();
                    parts.push(part)
                }
                _ => todo!(), // type error
            }
        }

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let joined = parts.join(&string);
        self.push_str(joined);
    }

    pub fn str_len(&mut self) {
        let len = (*(self.pop_str())).borrow().len();
        self.push_int(len as isize);
    }

    pub fn str_lower(&mut self) {
        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();
        self.push_str(string.to_lowercase());
    }

    pub fn str_upper(&mut self) {
        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();
        self.push_str(string.to_uppercase());
    }

    pub fn str_replace(&mut self) {
        let replace_rc = self.pop_str();
        let replace = (*replace_rc).borrow();

        let search_rc = self.pop_str();
        let search = (*search_rc).borrow();

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let replaced = search.replace(&*search, &replace);
        self.push_str(replaced);
    }

    pub fn str_split(&mut self) {
        let sep_rc = self.pop_str();
        let sep = (*sep_rc).borrow();

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let split: Vec<VariableEnum<T>> = string
            .split(&*sep)
            .map(|s| VariableEnum::Builtin(Variable::String(Rc::new(RefCell::new(s.to_owned())))))
            .collect();
        self.push_vector(Vector::from(split));
    }

    pub fn str_strip(&mut self) {
        todo!(); // TODO remove or rename this
    }

    pub fn str_find_after(&mut self) {
        let start = self.pop_int() as usize;

        let search_rc = self.pop_str();
        let search = (*search_rc).borrow();

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        // TODO what happens if start < 0 or start >= string.len() ?

        let found = string[start..].find(&*search).map(|i| i + start);

        self.push_int(found.unwrap_or(0) as isize);
        self.push_bool(found.is_some());
    }

    pub fn str_find(&mut self) {
        let search_rc = self.pop_str();
        let search = (*search_rc).borrow();

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let found = string.find(&*search);

        self.push_int(found.unwrap_or(0) as isize);
        self.push_bool(found.is_some());
    }

    pub fn str_substr(&mut self) {
        let end = self.pop_int() as usize;
        let start = self.pop_int() as usize;

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        // TODO be sure to fail in controlled manner if this doesn't hold: start <= end <= string.len()

        let substr = string[start..end].to_owned();
        self.push_str(substr);
    }

    pub fn str_to_bool(&mut self) {
        todo!(); // Decide if we want to keep this at all
    }

    pub fn str_to_int(&mut self) {
        // TODO Decide if we want to keep this at all

        let string_rc = self.pop_str();
        let string = &*string_rc.borrow();

        match string.parse::<isize>() {
            Ok(integer) => {
                self.push_int(integer);
                self.push_bool(true);
            }
            Err(_) => {
                self.push_int(0);
                self.push_bool(false);
            }
        }
    }

    pub fn vec_copy(&mut self) {
        todo!();
    }

    pub fn map_copy(&mut self) {
        todo!();
    }

    pub fn fsync(&mut self) {
        todo!(); // will be removed, there is no Rust equivalent
    }

    pub fn environ(&mut self) {
        let mut env_vars = Map::new();
        for (key, val) in env::vars_os() {
            // Use pattern bindings instead of testing .is_some() followed by .unwrap()
            if let (Ok(k), Ok(v)) = (key.into_string(), val.into_string()) {
                let key_var =
                    VariableEnum::Builtin(Variable::<T>::String(Rc::new(RefCell::new(k))));
                let value_var =
                    VariableEnum::Builtin(Variable::<T>::String(Rc::new(RefCell::new(v))));

                env_vars.insert(key_var, value_var);
            }
        }

        self.push_map(env_vars)
    }

    pub fn execve(&mut self) {
        todo!(); // Consider using nix
    }

    pub fn fork(&mut self) {
        todo!(); // Consider using nix
    }

    pub fn waitpid(&mut self) {
        todo!(); // Consider using nix
    }

    pub fn getcwd(&mut self) {
        let dir = env::current_dir();

        match dir {
            Ok(dir) => {
                let path: String = dir.to_str().unwrap().to_owned(); // TODO remove unwrap(), figure out what can fail
                self.push_str(path);
            }
            Err(_) => todo!(), // getcwd() can fail, but the signature doesn't reflect that
        }
    }

    pub fn chdir(&mut self) {
        let path_str_rc = self.pop_str();
        let path_str = &*(*path_str_rc).borrow();
        let path = Path::new(&path_str);

        let success = env::set_current_dir(path).is_ok();
        self.push_bool(success);
    }

    pub fn close(&mut self) {
        todo!(); // remove this or use nix
    }

    pub fn getpid(&mut self) {
        let pid = process::id();
        self.push_int(pid as isize);
    }

    pub fn getppid(&mut self) {
        todo!(); // use nix
    }

    pub fn getenv(&mut self) {
        let name_rc = self.pop_str();
        let name = (*name_rc).borrow();

        let value = env::var(&*name);

        match value {
            Ok(value) => {
                self.push_str(value);
                self.push_bool(true);
            }
            Err(_) => {
                self.push_str(String::from(""));
                self.push_bool(false);
            }
        }
    }

    pub fn assign(&mut self, var: &mut VariableEnum<T>) {
        let popped = self.pop();
        *var = popped;
    }

    pub fn gettimeofday(&mut self) {
        // TODO consider renaming gettimeofday to time
        let now = SystemTime::now();

        match now.duration_since(UNIX_EPOCH) {
            Ok(duration) => {
                let duration_micro_sec = duration.as_micros();
                self.push_int((duration_micro_sec / 1_000_000) as isize);
                self.push_int((duration_micro_sec % 1_000_000) as isize);
            }
            Err(_) => todo!(), // do we just crash here?
        }
    }

    pub fn open(&mut self) {
        todo!(); // remove or use nix
    }

    pub fn setenv(&mut self) {
        let value_rc = self.pop_str();
        let value = value_rc.borrow();

        let name_rc = self.pop_str();
        let name = name_rc.borrow();

        env::set_var(&*name, &*value);
    }

    pub fn time(&mut self) {
        todo!(); // will be removed
    }

    pub fn unlink(&mut self) {
        let path_rc = self.pop_str();
        let path = path_rc.borrow();

        self.push_bool(fs::remove_file(&*path).is_ok());
    }

    pub fn unsetenv(&mut self) {
        let name_rc = self.pop_str();
        let name = name_rc.borrow();

        env::remove_var(&*name);
    }

    pub fn vec_iter(&mut self) {
        let vector_rc = self.pop_vector();
        let iter = vector_rc.borrow_mut().iter();

        self.push_vector_iter(iter);
    }

    pub fn vec_iter_next(&mut self) {
        let vector_iter_rc = self.pop_vector_iterator();
        let mut vector_iter = vector_iter_rc.borrow_mut();

        match vector_iter.next() {
            Some(var) => {
                self.push(var);
                self.push_bool(true);
            }
            None => {
                self.push_none();
                self.push_bool(false);
            }
        }
    }

    pub fn map_iter(&mut self) {
        let map_rc = self.pop_map();
        let iter = map_rc.borrow_mut().iter();

        self.push_map_iter(iter);
    }

    pub fn map_iter_next(&mut self) {
        let map_iter_rc = self.pop_map_iterator();
        let mut map_iter = map_iter_rc.borrow_mut();

        match map_iter.next() {
            Some((key, value)) => {
                self.push(key);
                self.push(value);
                self.push_bool(true);
            }
            None => {
                self.push_none();
                self.push_none();
                self.push_bool(false);
            }
        }
    }

    pub fn set_add(&mut self) {
        let item = self.pop();
        let set_rc = self.pop_set();
        let mut set = set_rc.borrow_mut();

        set.insert(item, ());
    }

    pub fn set_has(&mut self) {
        let item = self.pop();
        let set_rc = self.pop_set();
        let set = set_rc.borrow();

        let found = set.contains_key(&item);
        self.push_bool(found);
    }

    pub fn set_clear(&mut self) {
        let set_rc = self.pop_set();
        let mut set = set_rc.borrow_mut();

        set.clear();
    }

    pub fn set_copy(&mut self) {
        todo!();
    }

    pub fn set_empty(&mut self) {
        let set_rc = self.pop_set();
        let set = set_rc.borrow();

        self.push_bool(set.is_empty());
    }

    pub fn set_iter(&mut self) {
        let set_rc = self.pop_set();
        let iter = set_rc.borrow_mut().iter();

        self.push_set_iter(iter);
    }

    pub fn set_remove(&mut self) {
        let item = self.pop();
        let set_rc = self.pop_map();
        let mut set = set_rc.borrow_mut();

        set.remove_entry(&item);
    }

    pub fn set_size(&mut self) {
        let set_rc = self.pop_set();
        let size = set_rc.borrow().len();

        self.push_int(size as isize);
    }

    pub fn set_iter_next(&mut self) {
        let set_iter_rc = self.pop_set_iterator();
        let mut set_iter = set_iter_rc.borrow_mut();

        match set_iter.next() {
            Some((item, _)) => {
                self.push(item);
                self.push_bool(true);
            }
            None => {
                self.push_none();
                self.push_bool(false);
            }
        }
    }

    pub fn copy(&mut self) {
        todo!();
    }

    pub fn make_const(&mut self) {
        // NOTE this doesn't do anything

        // TODO don't generate calls to this function in transpiler
    }
}
