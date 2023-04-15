// TODO remove
#![allow(dead_code)]
#![allow(unused_variables)]
#![allow(unreachable_code)]

use std::{
    cell::RefCell,
    env,
    ffi::CString,
    fmt::{Debug, Formatter, Result},
    fs,
    net::{Ipv4Addr, ToSocketAddrs},
    path::Path,
    process,
    rc::Rc,
    str::FromStr,
    time::{SystemTime, UNIX_EPOCH},
    vec,
};

use nix::{
    sys::{
        socket::{
            accept, bind, connect, getpeername, listen, socket, AddressFamily, SockFlag, SockType,
            SockaddrIn,
        },
        wait::{WaitPidFlag, WaitStatus},
    },
    unistd::{self, read, ForkResult, Pid},
};

use crate::{
    map::{Map, MapIterator},
    set::{Set, SetIterator},
    var::Enum,
    vector::VectorIterator,
};
use crate::{
    var::{Struct, Variable},
    vector::Vector,
};

pub struct Stack {
    items: Vec<Variable>,
}

impl Debug for Stack {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "Stack ({}):", self.len())?;
        for item in self.items.iter() {
            write!(f, " ")?;
            write!(f, "{:?}", item)?;
        }
        Ok(())
    }
}

impl Stack {
    pub fn new() -> Self {
        Self { items: Vec::new() }
    }

    pub fn from_argv() -> Self {
        let mut stack = Self::new();
        let mut arg_vector = Vector::new();
        for arg in env::args().into_iter() {
            arg_vector.push(Variable::String(Rc::new(RefCell::new(arg))));
        }
        stack.push_vector(arg_vector);
        stack
    }

    pub fn push(&mut self, v: Variable) {
        self.items.push(v);
    }

    fn len(&self) -> usize {
        self.items.len()
    }

    fn type_error(&self, message: &str) -> ! {
        eprintln!("Type error: {}", message);
        process::exit(1);
    }

    fn pop_type_error(&self, expected_type: &str, found: &Variable) -> ! {
        let found = found.kind();
        let msg = format!("pop failed, expected {expected_type}, found {found}");
        self.type_error(&msg);
    }

    fn type_error_vec_str(&self, v: &Variable) {
        let found = v.kind();
        let msg = format!("expected vec[str], but found {found} in vec");
        self.type_error(&msg);
    }

    pub fn push_int(&mut self, v: isize) {
        let item = Variable::Integer(v);
        self.push(item);
    }

    pub fn push_bool(&mut self, v: bool) {
        let item = Variable::Boolean(v);
        self.push(item);
    }

    pub fn push_str(&mut self, v: &str) {
        let item = Variable::String(Rc::new(RefCell::new(String::from(v))));
        self.push(item);
    }

    pub fn push_vector(&mut self, v: Vector<Variable>) {
        let item = Variable::Vector(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_set(&mut self, v: Set<Variable>) {
        let item = Variable::Set(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_map(&mut self, v: Map<Variable, Variable>) {
        let item = Variable::Map(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_struct(&mut self, v: Struct) {
        let item = Variable::Struct(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_vector_iter(&mut self, v: VectorIterator<Variable>) {
        let item = Variable::VectorIterator(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_map_iter(&mut self, v: MapIterator<Variable, Variable>) {
        let item = Variable::MapIterator(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_set_iter(&mut self, v: SetIterator<Variable>) {
        let item = Variable::SetIterator(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_none(&mut self) {
        self.push(Variable::None);
    }

    pub fn push_enum(&mut self, v: Enum) {
        self.push(Variable::Enum(Rc::new(RefCell::new(v))));
    }

    pub fn pop(&mut self) -> Variable {
        match self.items.pop() {
            Some(popped) => popped,
            None => self.type_error("cannot pop from empty stack"),
        }
    }

    fn top(&mut self) -> &Variable {
        match self.items.last() {
            None => self.type_error("cannot get top of empty stack"),
            Some(v) => v,
        }
    }

    pub fn pop_int(&mut self) -> isize {
        match self.pop() {
            Variable::Integer(v) => v,
            v => self.pop_type_error("int", &v),
        }
    }

    pub fn pop_bool(&mut self) -> bool {
        match self.pop() {
            Variable::Boolean(v) => v,
            v => self.pop_type_error("bool", &v),
        }
    }

    pub fn pop_str(&mut self) -> Rc<RefCell<String>> {
        match self.pop() {
            Variable::String(v) => v,
            v => self.pop_type_error("str", &v),
        }
    }

    pub fn pop_vector(&mut self) -> Rc<RefCell<Vector<Variable>>> {
        match self.pop() {
            Variable::Vector(v) => v,
            v => self.pop_type_error("vec", &v),
        }
    }

    pub fn pop_set(&mut self) -> Rc<RefCell<Set<Variable>>> {
        match self.pop() {
            Variable::Set(v) => v,
            v => self.pop_type_error("set", &v),
        }
    }

    pub fn pop_map(&mut self) -> Rc<RefCell<Map<Variable, Variable>>> {
        match self.pop() {
            Variable::Map(v) => v,
            v => self.pop_type_error("map", &v),
        }
    }

    pub fn pop_struct(&mut self) -> Rc<RefCell<Struct>> {
        match self.pop() {
            Variable::Struct(v) => v,
            v => self.pop_type_error("struct", &v),
        }
    }

    pub fn pop_vector_iterator(&mut self) -> Rc<RefCell<VectorIterator<Variable>>> {
        match self.pop() {
            Variable::VectorIterator(v) => v,
            v => self.pop_type_error("vec_iter", &v),
        }
    }

    pub fn pop_map_iterator(&mut self) -> Rc<RefCell<MapIterator<Variable, Variable>>> {
        match self.pop() {
            Variable::MapIterator(v) => v,
            v => self.pop_type_error("map_iter", &v),
        }
    }

    pub fn pop_set_iterator(&mut self) -> Rc<RefCell<SetIterator<Variable>>> {
        match self.pop() {
            Variable::SetIterator(v) => v,
            v => self.pop_type_error("set_iter", &v),
        }
    }

    pub fn pop_enum(&mut self) -> Rc<RefCell<Enum>> {
        match self.pop() {
            Variable::Enum(v) => v,
            v => self.pop_type_error("enum", &v),
        }
    }

    pub fn print(&mut self) {
        let top = self.pop();
        print!("{top}");
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
        self.push_str(&repr);
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
        // NOTE: protocol is not used
        let protocol = self.pop_int();

        let type_ = self.pop_int();
        let family = self.pop_int();

        // TODO This is very clunky.
        let family = AddressFamily::from_i32(family as i32).unwrap();
        let type_ = SockType::try_from(type_ as i32).unwrap();

        let result = socket(family, type_, SockFlag::empty(), None);

        self.push_int(result.unwrap_or(0) as isize);
        self.push_bool(result.is_ok());
    }

    pub fn exit(&mut self) -> ! {
        let code = self.pop_int();
        process::exit(code as i32);
    }

    pub fn write(&mut self) {
        let data_rc = self.pop_str();
        let data = &*data_rc.borrow();

        let fd = self.pop_int();
        let data = data.clone();

        let result = unistd::write(fd as i32, data.as_bytes());

        self.push_int(result.unwrap_or(0) as isize);
        self.push_bool(result.is_ok());
    }

    pub fn connect(&mut self) {
        let port = self.pop_int();

        let domain_rc = self.pop_str();
        let domain = &*domain_rc.borrow();

        let fd = self.pop_int();

        // TODO move domain name resolving out of this function, consider creating a dedicated stdlib func for this
        let authority = &format!("{domain}:{port}");

        let socket_addr = match authority.to_socket_addrs() {
            Err(_) => {
                self.push_bool(false);
                return;
            }
            Ok(mut socket_addr_iter) => match socket_addr_iter.next() {
                Some(socket_addr) => socket_addr,
                None => {
                    self.push_bool(false);
                    return;
                }
            },
        };

        let ip_addr = socket_addr.ip().to_string();

        let addr = SockaddrIn::from_str(&format!("{ip_addr}:{port}")).unwrap();

        let result = connect(fd as i32, &addr);

        self.push_bool(result.is_ok());
    }

    pub fn read(&mut self) {
        let n = self.pop_int();
        let fd = self.pop_int();

        let mut buffer = vec![0u8; n as usize];

        let result = read(fd as i32, &mut buffer[..]);

        match result {
            Ok(read_bytes) => {
                let string = String::from_utf8(buffer);

                match string {
                    Ok(string) => {
                        self.push_str(&string);
                        self.push_bool(true);
                    }
                    Err(_) => {
                        self.push_str("");
                        self.push_bool(false);
                    }
                }
            }
            Err(_) => {
                self.push_str("");
                self.push_bool(false);
            }
        }
    }

    pub fn bind(&mut self) {
        let port = self.pop_int();
        let ip_addr_rc = self.pop_str();
        let ip_addr = &*ip_addr_rc.borrow();
        let fd = self.pop_int();

        let addr = SockaddrIn::from_str(&format!("{ip_addr}:{port}")).unwrap();

        let result = bind(fd as i32, &addr);
        self.push_bool(result.is_ok());
    }

    pub fn listen(&mut self) {
        let backlog = self.pop_int();
        let fd = self.pop_int();

        let result = listen(fd as i32, backlog as usize);
        self.push_bool(result.is_ok());
    }

    pub fn accept(&mut self) {
        let fd = self.pop_int();
        let result = accept(fd as i32);

        match result {
            Ok(fd) => {
                let addr: nix::Result<SockaddrIn> = getpeername(fd);
                match addr {
                    Err(_) => {
                        self.push_str("");
                        self.push_int(0);
                        self.push_int(0);
                        self.push_bool(false);
                    }
                    Ok(addr) => {
                        let ip = addr.ip();
                        let ip = Ipv4Addr::from(ip).to_string();

                        let port = addr.port();

                        self.push_str(&ip);
                        self.push_int(port as isize);
                        self.push_int(fd as isize);
                        self.push_bool(true);
                    }
                }
            }
            Err(_) => {
                self.push_str("");
                self.push_int(0);
                self.push_int(0);
                self.push_bool(false);
            }
        }
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
            None => self.type_error("cannot pop from empty vector"),
        }
    }

    pub fn vec_get_copy(&mut self) {
        // TODO rename to vec_get
        let offset = self.pop_int();

        let vector_rc = self.pop_vector();
        let vector = (*vector_rc).borrow();

        let gotten = vector.get(offset as usize);
        self.push(gotten.clone_recursive());
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

    pub fn map_get_copy(&mut self) {
        // TODO rename to map_get
        let key = self.pop();
        let map_rc = self.pop_map();
        let map = map_rc.borrow_mut();

        match map.get(&key) {
            None => {
                self.push(Variable::None);
                self.push_bool(false);
            }
            Some(value) => {
                self.push(value.clone_recursive());
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
            None => {
                self.push(Variable::None);
                self.push_bool(false);
            }
            Some((k, v)) => {
                self.push(v);
                self.push_bool(true);
            }
        }
    }

    pub fn map_drop(&mut self) {
        let key = self.pop();
        let map_rc = self.pop_map();
        let mut map = map_rc.borrow_mut();

        let result = map.remove_entry(&key);
        self.push_bool(result.is_some());
    }

    pub fn str_append(&mut self) {
        let rhs_rc = self.pop_str();
        let rhs = (*rhs_rc).borrow();

        let lhs_rc = self.pop_str();
        let lhs = (*lhs_rc).borrow();

        let combined = lhs.clone() + &rhs;
        self.push_str(&combined);
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
                Variable::String(part) => {
                    let part = (*part).borrow().clone();
                    parts.push(part)
                }
                v => self.type_error_vec_str(&v),
            }
        }

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let joined = parts.join(&string);
        self.push_str(&joined);
    }

    pub fn str_len(&mut self) {
        let len = (*(self.pop_str())).borrow().len();
        self.push_int(len as isize);
    }

    pub fn str_lower(&mut self) {
        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();
        self.push_str(&string.to_lowercase());
    }

    pub fn str_upper(&mut self) {
        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();
        self.push_str(&string.to_uppercase());
    }

    pub fn str_replace(&mut self) {
        let replace_rc = self.pop_str();
        let replace = (*replace_rc).borrow();

        let search_rc = self.pop_str();
        let search = (*search_rc).borrow();

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let replaced = string.replace(&*search, &replace);
        self.push_str(&replaced);
    }

    pub fn str_split(&mut self) {
        let sep_rc = self.pop_str();
        let sep = (*sep_rc).borrow();

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let split: Vec<Variable> = string
            .split(&*sep)
            .map(|s| Variable::String(Rc::new(RefCell::new(s.to_owned()))))
            .collect();
        self.push_vector(Vector::from(split));
    }

    pub fn str_strip(&mut self) {
        let string_rc = self.pop_str();
        let string = &*string_rc.borrow();

        let trimmed = string.trim();

        self.push_str(trimmed);
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
        let end = self.pop_int();
        let start = self.pop_int();

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        if !(0 <= start && start <= end && end as usize <= string.len()) {
            self.push_str("");
            self.push_bool(false);
            return;
        }

        let substr = &string[start as usize..end as usize];
        self.push_str(substr);
        self.push_bool(true);
    }

    pub fn str_to_bool(&mut self) {
        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        match string.as_str() {
            "true" => {
                self.push_bool(true);
                self.push_bool(true);
            }
            "false" => {
                self.push_bool(false);
                self.push_bool(true);
            }
            _ => {
                self.push_bool(false);
                self.push_bool(false);
            }
        }
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
        let vector = self.pop();

        match vector {
            Variable::Vector(_) => (),
            _ => self.pop_type_error("vec", &vector),
        }

        let copy = vector.clone_recursive();
        self.push(copy);
    }

    pub fn map_copy(&mut self) {
        let map = self.pop();

        match map {
            Variable::Map(_) => (),
            _ => self.pop_type_error("map", &map),
        }

        let copy = map.clone_recursive();
        self.push(copy);
    }

    pub fn struct_field_query(&mut self, field_name: &str) {
        let struct_rc = self.pop_struct();
        let struct_ = &*struct_rc.borrow();

        let value = struct_.values[field_name].clone();
        self.push(value);
    }

    pub fn struct_field_update(&mut self, field_name: &str) {
        let value = self.pop();

        let struct_rc = self.pop_struct();
        let mut struct_ = struct_rc.borrow_mut();

        struct_.values.insert(String::from(field_name), value);
    }

    pub fn fsync(&mut self) {
        todo!(); // will be removed, there is no Rust equivalent
    }

    pub fn environ(&mut self) {
        let mut env_vars = Map::new();
        for (key, val) in env::vars_os() {
            // Use pattern bindings instead of testing .is_some() followed by .unwrap()
            if let (Ok(k), Ok(v)) = (key.into_string(), val.into_string()) {
                let key_var = Variable::String(Rc::new(RefCell::new(k)));
                let value_var = Variable::String(Rc::new(RefCell::new(v)));

                env_vars.insert(key_var, value_var);
            }
        }

        self.push_map(env_vars)
    }

    pub fn execve(&mut self) {
        let env_rc = self.pop_map();
        let popped_env = &*env_rc.borrow();

        let mut env: Vec<CString> = vec![];

        for (key, value) in popped_env.iter() {
            env.push(CString::new(format!("{key:}={value:}")).unwrap())
        }

        let argv_rc = self.pop_vector();
        let popped_argv = &*argv_rc.borrow();

        let mut argv: Vec<CString> = vec![];
        for item in popped_argv.iter() {
            match item {
                Variable::String(v) => {
                    let string = &*v.borrow();
                    argv.push(CString::new(string.as_str()).unwrap())
                }
                v => self.type_error_vec_str(&v),
            }
        }

        let path_rc = self.pop_str();
        let path = &*path_rc.borrow();
        let path = CString::new(path.as_str()).unwrap();

        let result = unistd::execve(&path, &argv, &env);

        match result {
            Ok(_) => (), // Cannot happen
            Err(_) => self.push_bool(false),
        }
    }

    pub fn fork(&mut self) {
        let result = unsafe { unistd::fork() };
        match result {
            Ok(ForkResult::Parent { child }) => self.push_int(child.as_raw() as isize),
            Ok(ForkResult::Child) => self.push_int(0),
            Err(_) => todo!(), // Change signature to handle errors
        }
    }

    pub fn waitpid(&mut self) {
        // TODO use Aaa enums for return value
        let options = self.pop_int();
        let pid = self.pop_int();

        let options = match options {
            0 => None,
            v => Some(WaitPidFlag::from_bits_truncate(v as i32)),
        };

        let pid = Some(Pid::from_raw(pid as i32));

        let result = nix::sys::wait::waitpid(pid, options);

        match result {
            Err(_) => {
                self.push_int(0);
                self.push_int(0);
                self.push_bool(false);
                self.push_bool(false);
            }
            Ok(WaitStatus::Exited(pid, exit_code)) => {
                self.push_int(pid.as_raw() as isize);
                self.push_int(exit_code as isize);
                self.push_bool(true);
                self.push_bool(true);
            }
            Ok(_) => todo!(),
        }
    }

    pub fn getcwd(&mut self) {
        let dir = env::current_dir();

        match dir {
            Ok(dir) => {
                let path: String = dir.to_str().unwrap().to_owned(); // TODO remove unwrap(), figure out what can fail
                self.push_str(&path);
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
        let ppid = unistd::getppid().as_raw();
        self.push_int(ppid as isize);
    }

    pub fn getenv(&mut self) {
        let name_rc = self.pop_str();
        let name = (*name_rc).borrow();

        let value = env::var(&*name);

        match value {
            Ok(value) => {
                self.push_str(&value);
                self.push_bool(true);
            }
            Err(_) => {
                self.push_str("");
                self.push_bool(false);
            }
        }
    }

    pub fn assign(&mut self, var: &mut Variable) {
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

    pub fn unlink(&mut self) {
        let path_rc = self.pop_str();
        let path = path_rc.borrow().clone();

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
        let top = self.top();
        let copy = top.clone_recursive();
        self.push(copy);
    }

    pub fn make_const(&mut self) {
        // NOTE this doesn't do anything

        // TODO don't generate calls to this function in transpiler
    }

    pub fn get_enum_discriminant(&mut self) -> usize {
        let enum_rc = self.pop_enum();
        let enum_ = &*enum_rc.borrow();
        self.push(enum_.value.clone());
        enum_.discriminant
    }
}
