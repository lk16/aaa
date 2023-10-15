use std::{
    cell::RefCell,
    env,
    ffi::CString,
    fmt::{Display, Formatter, Result},
    fs,
    io::{stdout, Write},
    net::{Ipv4Addr, ToSocketAddrs},
    path::Path,
    process,
    rc::Rc,
    str::FromStr,
    thread::sleep,
    time::{Duration, SystemTime, UNIX_EPOCH},
    vec,
};

use nix::{
    fcntl::{open, OFlag},
    sys::{
        socket::{
            accept, bind, connect, getpeername, listen, socket, AddressFamily, SockFlag, SockType,
            SockaddrIn,
        },
        stat::Mode,
        wait::{WaitPidFlag, WaitStatus},
    },
    unistd::{self, close, read, ForkResult, Pid},
};
use regex::Regex;

use crate::{
    map::{Map, MapIterator},
    set::{Set, SetIterator, SetValue},
    vector::VectorIterator,
};
use crate::{
    var::{UserType, Variable},
    vector::Vector,
};

pub struct Stack<T>
where
    T: UserType,
{
    items: Vec<Variable<T>>,
}

impl<T> Display for Stack<T>
where
    T: UserType,
{
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "Stack ({}):", self.len())?;
        for item in self.items.iter() {
            write!(f, " ")?;
            write!(f, "{}", item)?;
        }
        Ok(())
    }
}

impl<T> Default for Stack<T>
where
    T: UserType,
{
    fn default() -> Self {
        Self::new()
    }
}

impl<T> Stack<T>
where
    T: UserType,
{
    pub fn new() -> Self {
        Self { items: Vec::new() }
    }

    pub fn from_argv() -> Self {
        let mut stack = Self::new();
        let mut arg_vector = Vector::new();
        for arg in env::args() {
            arg_vector.push(Variable::String(Rc::new(RefCell::new(arg))));
        }
        stack.push_vector(arg_vector);
        stack
    }

    pub fn push(&mut self, v: Variable<T>) {
        self.items.push(v);
    }

    fn len(&self) -> usize {
        self.items.len()
    }

    fn type_error(&self, message: &str) -> ! {
        eprintln!("Type error: {}", message);
        process::exit(1);
    }

    fn pop_type_error(&self, expected_type: &str, found: &Variable<T>) -> ! {
        let found = found.kind();
        let msg = format!("pop failed, expected {expected_type}, found {found}");
        self.type_error(&msg);
    }

    fn type_error_vec_str(&self, v: &Variable<T>) {
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

    pub fn push_vector(&mut self, v: Vector<Variable<T>>) {
        let item = Variable::Vector(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_set(&mut self, v: Set<Variable<T>>) {
        let item = Variable::Set(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_map(&mut self, v: Map<Variable<T>, Variable<T>>) {
        let item = Variable::Map(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_vector_iter(&mut self, v: VectorIterator<Variable<T>>) {
        let item = Variable::VectorIterator(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_map_iter(&mut self, v: MapIterator<Variable<T>, Variable<T>>) {
        let item = Variable::MapIterator(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_set_iter(&mut self, v: SetIterator<Variable<T>>) {
        let item = Variable::SetIterator(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_none(&mut self) {
        self.push(Variable::None);
    }

    pub fn push_regex(&mut self, v: Regex) {
        self.push(Variable::Regex(Rc::new(RefCell::new(v))));
    }

    pub fn push_user_type(&mut self, v: T) {
        self.push(Variable::UserType(Rc::new(RefCell::new(v))));
    }

    pub fn push_function_pointer(&mut self, func: fn(&mut Stack<T>)) {
        self.push(Variable::FunctionPointer(func));
    }

    pub fn pop(&mut self) -> Variable<T> {
        match self.items.pop() {
            Some(popped) => popped,
            None => self.type_error("cannot pop from empty stack"),
        }
    }

    fn top(&mut self) -> &Variable<T> {
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

    pub fn pop_vec(&mut self) -> Rc<RefCell<Vector<Variable<T>>>> {
        match self.pop() {
            Variable::Vector(v) => v,
            v => self.pop_type_error("vec", &v),
        }
    }

    pub fn pop_set(&mut self) -> Rc<RefCell<Set<Variable<T>>>> {
        match self.pop() {
            Variable::Set(v) => v,
            v => self.pop_type_error("set", &v),
        }
    }

    pub fn pop_map(&mut self) -> Rc<RefCell<Map<Variable<T>, Variable<T>>>> {
        match self.pop() {
            Variable::Map(v) => v,
            v => self.pop_type_error("map", &v),
        }
    }

    pub fn pop_vector_iterator(&mut self) -> Rc<RefCell<VectorIterator<Variable<T>>>> {
        match self.pop() {
            Variable::VectorIterator(v) => v,
            v => self.pop_type_error("vec_iter", &v),
        }
    }

    pub fn pop_map_iterator(&mut self) -> Rc<RefCell<MapIterator<Variable<T>, Variable<T>>>> {
        match self.pop() {
            Variable::MapIterator(v) => v,
            v => self.pop_type_error("map_iter", &v),
        }
    }

    pub fn pop_set_iterator(&mut self) -> Rc<RefCell<SetIterator<Variable<T>>>> {
        match self.pop() {
            Variable::SetIterator(v) => v,
            v => self.pop_type_error("set_iter", &v),
        }
    }

    pub fn pop_regex(&mut self) -> Rc<RefCell<Regex>> {
        match self.pop() {
            Variable::Regex(v) => v,
            v => self.pop_type_error("regex", &v),
        }
    }

    pub fn pop_user_type(&mut self) -> Rc<RefCell<T>> {
        match self.pop() {
            Variable::UserType(v) => v,
            v => self.pop_type_error("user_type", &v),
        }
    }

    pub fn pop_function_pointer(&mut self) -> fn(&mut Stack<T>) {
        match self.pop() {
            Variable::FunctionPointer(v) => v,
            v => self.pop_type_error("func_ptr", &v),
        }
    }

    pub fn pop_function_pointer_and_call(&mut self) {
        let func = self.pop_function_pointer();
        func(self);
    }

    pub fn print(&mut self) {
        let top = self.pop();
        print!("{top}");
        _ = stdout().flush(); // TODO remove when #67 `fflush` is added
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
        // used when called via function pointer
        self.assert_with_position(None)
    }

    pub fn assert_with_position(&mut self, position: Option<(&str, isize, isize)>) {
        // used when called directly

        if !self.pop_bool() {
            match position {
                Some((file, line, col)) => {
                    eprintln!("Assertion failure at {}:{}:{}", file, line, col)
                }
                None => eprintln!("Assertion failure at ??:??:??"),
            }
            process::exit(1);
        }
    }

    pub fn todo(&mut self) {
        // used when called via function pointer
        self.todo_with_position(None)
    }

    pub fn todo_with_position(&mut self, position: Option<(&str, isize, isize)>) {
        // used when called directly

        match position {
            Some((file, line, col)) => {
                eprintln!("Code at {}:{}:{} is not implemented", file, line, col)
            }
            None => eprintln!("Code at ??:??:?? is not implemented"),
        }
        process::exit(1);
    }

    pub fn unreachable(&mut self) {
        // used when called via function pointer
        self.unreachable_with_position(None)
    }

    pub fn unreachable_with_position(&mut self, position: Option<(&str, isize, isize)>) {
        // used when called directly

        match position {
            Some((file, line, col)) => {
                eprintln!("Code at {}:{}:{} should be unreachable", file, line, col)
            }
            None => eprintln!("Code at ??:??:?? should be unreachable"),
        }
        process::exit(1);
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
        let lhs: isize = self.pop_int();
        self.push_int(lhs.wrapping_mul(rhs));
    }

    pub fn divide(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();

        if rhs == 0 {
            panic!("Cannot divide by zero!");
        }

        self.push_int(lhs / rhs);
    }

    pub fn modulo(&mut self) {
        let rhs = self.pop_int();
        let lhs = self.pop_int();

        if rhs == 0 {
            panic!("Cannot use modulo zero!");
        }

        self.push_int(lhs % rhs);
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
        let _protocol = self.pop_int();

        let type_ = self.pop_int();
        let family = self.pop_int();

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

        // TODO #28 Move domain name resolving out of this function and create a dedicated stdlib func for this
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
            Ok(bytes_read) => {
                buffer.truncate(bytes_read);

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
        let vector = self.pop_vec();
        vector.borrow_mut().push(pushed);
    }

    pub fn vec_pop(&mut self) {
        let vector = self.pop_vec();
        let popped = vector.borrow_mut().pop();

        match popped {
            Some(popped) => self.push(popped),
            None => self.type_error("cannot pop from empty vector"),
        }
    }

    pub fn vec_get(&mut self) {
        let offset = self.pop_int();

        let vector_rc = self.pop_vec();
        let vector = (*vector_rc).borrow();

        let gotten = vector.get(offset as usize);
        self.push(gotten);
    }

    pub fn vec_set(&mut self) {
        let value = self.pop();
        let offset = self.pop_int();
        let vector = self.pop_vec();

        vector.borrow_mut().set(offset as usize, value);
    }

    pub fn vec_len(&mut self) {
        let len = (*(self.pop_vec())).borrow().len();
        self.push_int(len as isize);
    }

    pub fn vec_empty(&mut self) {
        let is_empty = (*(self.pop_vec())).borrow().is_empty();
        self.push_bool(is_empty);
    }

    pub fn vec_clear(&mut self) {
        self.pop_vec().borrow_mut().clear();
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
        let key = self.pop();
        let map_rc = self.pop_map();
        let map = map_rc.borrow_mut();

        match map.get(&key) {
            None => {
                self.push(Variable::None);
                self.push_bool(false);
            }
            Some(value) => {
                self.push(value);
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

    pub fn map_len(&mut self) {
        let len = (*(self.pop_map())).borrow().len();
        self.push_int(len as isize);
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
            Some((_, v)) => {
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
        let vector_rc = self.pop_vec();
        let vector = vector_rc.borrow();

        let mut parts = vec![];
        for part in vector.iter() {
            match part {
                Variable::String(part) => parts.push((*part.borrow()).clone()),
                v => self.type_error_vec_str(&v),
            }
        }

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let joined = parts.join(&string);
        self.push_str(&joined);
    }

    pub fn str_len(&mut self) {
        let len = (*(self.pop_str())).borrow().chars().count();
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

        let split: Vec<Variable<T>> = string
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
        let char_start = self.pop_int();
        let search_rc = self.pop_str();
        let string_rc = self.pop_str();

        self._str_find(string_rc, search_rc, char_start);
    }

    pub fn str_find(&mut self) {
        let search_rc = self.pop_str();
        let string_rc = self.pop_str();
        self._str_find(string_rc, search_rc, 0);
    }

    fn _str_find(
        &mut self,
        string_rc: Rc<RefCell<String>>,
        search_rc: Rc<RefCell<String>>,
        char_start: isize,
    ) {
        let string = (*string_rc).borrow();
        let search = (*search_rc).borrow();

        let byte_start = string
            .char_indices()
            .nth(char_start as usize)
            .map(|(byte_index, _)| byte_index);

        let found = if let Some(byte_start) = byte_start {
            string[byte_start..].find(&*search).map(|i| i + byte_start)
        } else {
            // start out of range
            self.push_int(0);
            self.push_bool(false);
            return;
        };

        match found {
            Some(byte_offset) => {
                let char_offset = string
                    .char_indices()
                    .take_while(|(byte_idx, _)| *byte_idx < byte_offset)
                    .count();
                self.push_int(char_offset as isize);
                self.push_bool(true);
            }
            None => {
                // not found
                self.push_int(0);
                self.push_bool(false);
            }
        }
    }

    pub fn str_substr(&mut self) {
        let end = self.pop_int() as usize;
        let start = self.pop_int() as usize;

        let string_rc = self.pop_str();
        let string = (*string_rc).borrow();

        let start_byte_index = string
            .char_indices()
            .nth(start)
            .map(|(byte_index, _)| byte_index);

        let end_byte_index = if end == string.chars().count() {
            Some(string.len())
        } else {
            string
                .char_indices()
                .nth(end)
                .map(|(byte_index, _)| byte_index)
        };

        if let (Some(start), Some(end)) = (start_byte_index, end_byte_index) {
            if start > end {
                self.push_str("");
                self.push_bool(false);
                return;
            }

            self.push_str(&string[start..end]);
            self.push_bool(true);
        } else {
            self.push_str("");
            self.push_bool(false);
        }
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

        let argv_rc = self.pop_vec();
        let popped_argv = &*argv_rc.borrow();

        let mut argv: Vec<CString> = vec![];
        for item in popped_argv.iter() {
            match item {
                Variable::String(v) => argv.push(CString::new(v.borrow().as_str()).unwrap()),
                v => self.type_error_vec_str(&v),
            }
        }

        let path_rc = self.pop_str();
        let path = &*path_rc.borrow();
        let path = CString::new(path.as_str()).unwrap();

        let result = unistd::execve(&path, &argv, &env);

        match result {
            Ok(_) => unreachable!(),
            Err(_) => self.push_bool(false),
        }
    }

    pub fn fork(&mut self) {
        let result = unsafe { unistd::fork() };
        match result {
            Ok(ForkResult::Parent { child }) => self.push_int(child.as_raw() as isize),
            Ok(ForkResult::Child) => self.push_int(0),
            Err(_) => todo!(), // TODO #29 Change `fork` signature to handle errors
        }
    }

    pub fn waitpid(&mut self) {
        // TODO #30 Use Aaa enums for return value
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
            Ok(_) => todo!(), // TODO #30
        }
    }

    pub fn getcwd(&mut self) {
        let dir = env::current_dir();

        match dir {
            Ok(dir) => {
                let path: String = dir.to_str().unwrap().to_owned(); // TODO #31 remove unwrap(), figure out what can fail
                self.push_str(&path);
            }
            Err(_) => todo!(), // TODO #31 Update signature of `getcwd`, because it can fail
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
        let fd = self.pop_int();

        let result = close(fd as i32);

        self.push_bool(result.is_ok());
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

    pub fn assign(&mut self, var: &mut Variable<T>) {
        let popped = self.pop();
        *var = popped;
    }

    pub fn time(&mut self) {
        let now = SystemTime::now();

        match now.duration_since(UNIX_EPOCH) {
            Ok(duration) => {
                let duration_micro_sec = duration.as_micros();
                self.push_int((duration_micro_sec / 1_000_000) as isize);
                self.push_int((duration_micro_sec % 1_000_000) as isize);
            }
            Err(_) => unreachable!(),
        }
    }

    pub fn open(&mut self) {
        let mode = self.pop_int();
        let flag = self.pop_int();

        let path_rc = self.pop_str();
        let path = &*path_rc.borrow();
        let path = CString::new(path.as_str()).unwrap();

        let result = open(
            path.as_c_str(),
            OFlag::from_bits_truncate(flag as i32),
            Mode::from_bits_truncate(mode as u32),
        );

        self.push_int(result.unwrap_or(0) as isize);
        self.push_bool(result.is_ok());
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
        let vector_rc = self.pop_vec();
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

        set.insert(item, SetValue {});
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
        let set = self.pop();

        match set {
            Variable::Set(_) => (),
            _ => self.pop_type_error("set", &set),
        }

        let copy = set.clone_recursive();
        self.push(copy);
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

    pub fn set_len(&mut self) {
        let set_rc = self.pop_set();
        let len = set_rc.borrow().len();

        self.push_int(len as isize);
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

    pub fn sleep(&mut self) {
        let secs = self.pop_int();
        sleep(Duration::from_secs(secs as u64));
    }

    pub fn usleep(&mut self) {
        let micros = self.pop_int();
        sleep(Duration::from_micros(micros as u64));
    }

    pub fn make_regex(&mut self) {
        let pattern_rc = self.pop_str();
        let pattern = &*pattern_rc.borrow();
        match Regex::new(pattern) {
            Ok(regex) => {
                self.push_regex(regex);
                self.push_bool(true);
            }
            Err(_) => {
                self.push_none();
                self.push_bool(false);
            }
        }
    }

    pub fn regex_find(&mut self) {
        let offset = self.pop_int();
        let string_rc = self.pop_str();
        let string = &*string_rc.borrow();
        let regex_rc = self.pop_regex();
        let regex = regex_rc.borrow();

        let offset_byte_index = string
            .char_indices()
            .nth(offset as usize)
            .map(|(byte_index, _)| byte_index);

        let after_offset = if let Some(offset_byte_index) = offset_byte_index {
            &string[offset_byte_index..]
        } else {
            // offset is outside of range
            self.push_str("");
            self.push_int(0);
            self.push_bool(false);
            return;
        };

        let regex_match = regex.find(after_offset);

        match regex_match {
            Some(matched) => {
                let matched_byte_offset = matched.start();
                let matched_string = matched.as_str().to_owned();

                let matched_char_offset = string
                    .char_indices()
                    .take_while(|(byte_idx, _)| *byte_idx < matched_byte_offset)
                    .count();

                self.push_str(&matched_string);
                self.push_int(offset + matched_char_offset as isize);
                self.push_bool(true);
            }
            None => {
                // no match found
                self.push_str("");
                self.push_int(0);
                self.push_bool(false);
            }
        }
    }

    pub fn zero_function_pointer_value(&mut self) {
        // Function pointers must point to a function in Aaa.
        // The zero-value for function pointers is this function.
        // Since this should never happen in a correct program, we just crash with an error message.

        eprintln!("Function pointer with zero-value was called.");
        process::exit(1);
    }

    pub fn assert_stack_top_types(
        &mut self,
        file: &str,
        line: isize,
        column: isize,
        expected_top: Vec<&str>,
    ) {
        let mut ok = true;

        if self.items.len() < expected_top.len() {
            let found_stack_top = self
                .items
                .iter()
                .map(|i| i.kind())
                .collect::<Vec<_>>()
                .join(" ");

            eprintln!("Runtime type-checker failed at {file}:{line}:{column}");
            eprintln!("Expected stack top: {}", expected_top.join(" "));
            eprintln!("   Found stack top: {}", found_stack_top);
            process::exit(1);
        }

        let start_index = self.items.len() - expected_top.len();

        for (actual, expected) in self.items.iter().skip(start_index).zip(expected_top.iter()) {
            if actual.kind() != *expected && actual.kind() != "none" {
                // #33 Remove check for none
                ok = false;
            }
        }

        if !ok {
            let found_stack_top = self
                .items
                .iter()
                .skip(start_index)
                .map(|i| i.kind())
                .collect::<Vec<_>>()
                .join(" ");

            eprintln!("Runtime type-checker failed at {file}:{line}:{column}");
            eprintln!("Expected stack top: {}", expected_top.join(" "));
            eprintln!("   Found stack top: {}", found_stack_top);
            process::exit(1);
        }
    }
}
