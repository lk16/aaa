// TODO remove
#![allow(dead_code)]
#![allow(unused_variables)]
#![allow(unreachable_code)]

use std::{
    cell::RefCell,
    collections::{HashMap, HashSet},
    process,
    rc::Rc,
};

use crate::var::Variable;

pub struct Stack {
    items: Vec<Variable>,
}

impl Stack {
    pub fn new() -> Self {
        Self { items: Vec::new() }
    }

    fn push(&mut self, v: Variable) {
        self.items.push(v);
    }

    fn len(&self) -> usize {
        self.items.len()
    }

    pub fn push_int(&mut self, v: isize) {
        let item = Variable::Integer(v);
        self.push(item);
    }

    pub fn push_bool(&mut self, v: bool) {
        let item = Variable::Boolean(v);
        self.push(item);
    }

    pub fn push_str(&mut self, v: String) {
        let item = Variable::String(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_vector(&mut self, v: Vec<Variable>) {
        let item = Variable::Vector(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_set(&mut self, v: HashSet<Variable>) {
        let item = Variable::Set(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    pub fn push_map(&mut self, v: HashMap<Variable, Variable>) {
        let item = Variable::Map(Rc::new(RefCell::new(v)));
        self.push(item);
    }

    fn pop(&mut self) -> Variable {
        match self.items.pop() {
            Some(popped) => popped,
            None => todo!(), // TODO handle popping from empty stack
        }
    }

    fn top(&mut self) -> &Variable {
        match self.items.last() {
            None => todo!(),
            Some(v) => v,
        }
    }

    pub fn pop_int(&mut self) -> isize {
        match self.pop() {
            Variable::Integer(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_bool(&mut self) -> bool {
        match self.pop() {
            Variable::Boolean(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_str(&mut self) -> Rc<RefCell<String>> {
        match self.pop() {
            Variable::String(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_vector(&mut self) -> Rc<RefCell<Vec<Variable>>> {
        match self.pop() {
            Variable::Vector(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_set(&mut self) -> Rc<RefCell<HashSet<Variable>>> {
        match self.pop() {
            Variable::Set(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_map(&mut self) -> Rc<RefCell<HashMap<Variable, Variable>>> {
        match self.pop() {
            Variable::Map(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn print_top(&mut self) {
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
            panic!("Assertion failure!\n"); // TODO consider nicer alternatives
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
        let lhs = self.pop_int();
        let rhs = self.pop_int();
        self.push_int(lhs + rhs);
    }

    pub fn minus(&mut self) {
        let lhs = self.pop_int();
        let rhs = self.pop_int();
        self.push_int(lhs - rhs);
    }

    pub fn multiply(&mut self) {
        let lhs = self.pop_int();
        let rhs = self.pop_int();
        self.push_int(lhs * rhs);
    }

    pub fn divide(&mut self) {
        let lhs = self.pop_int();
        let rhs = self.pop_int();

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

    pub fn print(&mut self) {
        let top = self.pop();
        print!("{top:?}");
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

    pub fn push_vec_empty(&mut self) {
        self.push_vector(vec![]);
    }

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
        let vector = self.pop_vector();

        let gotten = vector.borrow()[offset as usize].clone();
        self.push(gotten);
    }

    pub fn vec_set(&mut self) {
        let value = self.pop();
        let offset = self.pop_int();
        let vector = self.pop_vector();

        vector.borrow_mut()[offset as usize] = value;
    }

    pub fn vec_size(&mut self) {
        let vector = self.pop_vector();
        self.push_int(vector.borrow().len() as isize);
    }

    pub fn vec_empty(&mut self) {
        let vector = self.pop_vector();
        self.push_bool(vector.borrow().is_empty());
    }

    pub fn vec_clear(&mut self) {
        self.pop_vector().borrow_mut().clear();
    }

    pub fn push_map_empty(&mut self) {
        self.push_map(HashMap::new())
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
        let map = self.pop_map();
        let has_key = map.borrow().contains_key(&key);
        self.push_bool(has_key);
    }

    fn map_size(&mut self) {
        let map = self.pop_map();
        self.push_int(map.borrow().len() as isize);
    }

    fn map_empty(&mut self) {
        let map = self.pop_map();
        self.push_bool(map.borrow().is_empty());
    }

    fn map_clear(&mut self) {
        self.pop_map().borrow_mut().clear();
    }

    fn map_pop(&mut self) {
        let key = self.pop();
        let map_rc = self.pop_map();
        let mut map = map_rc.borrow_mut();

        match map.remove_entry(&key) {
            None => todo!(), // In C we push NULL here, see also map_get_copy()
            Some((k, v)) => self.push(v),
        }
    }

    fn map_drop(&mut self) {
        let key = self.pop();
        let map_rc = self.pop_map();
        let mut map = map_rc.borrow_mut();

        match map.remove_entry(&key) {
            None => todo!(), // In C we push NULL here, see also map_get_copy()
            Some(_) => (),
        }
    }

    /*
    fn str_append(&mut self) {
        struct aaa_string *rhs = aaa_stack_pop_str(stack);
        struct aaa_string *lhs = aaa_stack_pop_str(stack);

        struct aaa_string *combined = aaa_string_append(lhs, rhs);
        aaa_stack_push_str(stack, combined);

        aaa_string_dec_ref(lhs);
        aaa_string_dec_ref(rhs);
    }

    fn str_contains(&mut self) {
        struct aaa_string *search = aaa_stack_pop_str(stack);
        struct aaa_string *string = aaa_stack_pop_str(stack);

        bool contained = aaa_string_contains(string, search);
        aaa_stack_push_bool(stack, contained);

        aaa_string_dec_ref(search);
        aaa_string_dec_ref(string);
    }

    fn str_equals(&mut self) {
        struct aaa_string *rhs = aaa_stack_pop_str(stack);
        struct aaa_string *lhs = aaa_stack_pop_str(stack);

        bool contained = aaa_string_equals(lhs, rhs);
        aaa_stack_push_bool(stack, contained);

        aaa_string_dec_ref(lhs);
        aaa_string_dec_ref(rhs);
    }

    fn str_join(&mut self) {
        struct aaa_vector *parts = aaa_stack_pop_vec(stack);
        struct aaa_string *string = aaa_stack_pop_str(stack);

        struct aaa_string *joined = aaa_string_join(string, parts);
        aaa_stack_push_str(stack, joined);

        aaa_vector_dec_ref(parts);
        aaa_string_dec_ref(string);
    }

    fn str_len(&mut self) {
        struct aaa_string *string = aaa_stack_pop_str(stack);

        size_t length = aaa_string_len(string);
        aaa_stack_push_int(stack, (int)length);

        aaa_string_dec_ref(string);
    }

    fn str_lower(&mut self) {
        struct aaa_string *string = aaa_stack_pop_str(stack);

        struct aaa_string *lower = aaa_string_lower(string);
        aaa_stack_push_str(stack, lower);

        aaa_string_dec_ref(string);
    }

    fn str_upper(&mut self) {
        struct aaa_string *string = aaa_stack_pop_str(stack);

        struct aaa_string *upper = aaa_string_upper(string);
        aaa_stack_push_str(stack, upper);

        aaa_string_dec_ref(string);
    }

    fn str_replace(&mut self) {
        struct aaa_string *replace = aaa_stack_pop_str(stack);
        struct aaa_string *search = aaa_stack_pop_str(stack);
        struct aaa_string *string = aaa_stack_pop_str(stack);

        struct aaa_string *replaced = aaa_string_replace(string, search, replace);
        aaa_stack_push_str(stack, replaced);

        aaa_string_dec_ref(replace);
        aaa_string_dec_ref(search);
        aaa_string_dec_ref(string);
    }

    fn str_split(&mut self) {
        struct aaa_string *sep = aaa_stack_pop_str(stack);
        struct aaa_string *string = aaa_stack_pop_str(stack);

        struct aaa_vector *split = aaa_string_split(string, sep);
        aaa_stack_push_vec(stack, split);

        aaa_string_dec_ref(sep);
        aaa_string_dec_ref(string);
    }

    fn str_strip(&mut self) {
        struct aaa_string *string = aaa_stack_pop_str(stack);

        struct aaa_string *stripped = aaa_string_strip(string);
        aaa_stack_push_str(stack, stripped);

        aaa_string_dec_ref(string);
    }

    fn str_find_after(&mut self) {
        int start = aaa_stack_pop_int(stack);
        struct aaa_string *search = aaa_stack_pop_str(stack);
        struct aaa_string *string = aaa_stack_pop_str(stack);

        size_t offset;
        bool success;
        aaa_string_find_after(string, search, (size_t)start, &offset, &success);
        aaa_stack_push_int(stack, (int)offset);
        aaa_stack_push_bool(stack, success);

        aaa_string_dec_ref(search);
        aaa_string_dec_ref(string);
    }

    fn str_find(&mut self) {
        struct aaa_string *search = aaa_stack_pop_str(stack);
        struct aaa_string *string = aaa_stack_pop_str(stack);

        bool success;
        size_t offset;
        aaa_string_find(string, search, &offset, &success);
        aaa_stack_push_int(stack, (int)offset);
        aaa_stack_push_bool(stack, success);

        aaa_string_dec_ref(search);
        aaa_string_dec_ref(string);
    }

    fn str_substr(&mut self) {
        int end = aaa_stack_pop_int(stack);
        int start = aaa_stack_pop_int(stack);
        struct aaa_string *string = aaa_stack_pop_str(stack);

        bool success;
        struct aaa_string *substr =
            aaa_string_substr(string, (size_t)start, (size_t)end, &success);
        aaa_stack_push_str(stack, substr);
        aaa_stack_push_bool(stack, success);

        aaa_string_dec_ref(string);
    }

    fn str_to_bool(&mut self) {
        struct aaa_string *string = aaa_stack_pop_str(stack);

        bool boolean, success;
        aaa_string_to_bool(string, &boolean, &success);
        aaa_stack_push_bool(stack, boolean);
        aaa_stack_push_bool(stack, success);

        aaa_string_dec_ref(string);
    }

    fn str_to_int(&mut self) {
        struct aaa_string *string = aaa_stack_pop_str(stack);

        bool success;
        int integer;
        aaa_string_to_int(string, &integer, &success);
        aaa_stack_push_int(stack, integer);
        aaa_stack_push_bool(stack, success);

        aaa_string_dec_ref(string);
    }

    fn vec_copy(&mut self) {
        struct aaa_vector *vec = aaa_stack_pop_vec(stack);

        struct aaa_vector *copy = aaa_vector_copy(vec);
        aaa_stack_push_vec(stack, copy);

        aaa_vector_dec_ref(vec);
    }

    fn map_copy(&mut self) {
        struct aaa_map *map = aaa_stack_pop_map(stack);

        struct aaa_map *copy = aaa_map_copy(map);
        aaa_stack_push_map(stack, copy);

        aaa_map_dec_ref(map);
    }

    fn field_query(&mut self) {
        struct aaa_string *field_name = aaa_stack_pop_str(stack);
        struct aaa_struct *s = aaa_stack_pop_struct(stack);

        const char *field_name_raw = aaa_string_raw(field_name);
        struct aaa_variable *field = aaa_struct_get_field(s, field_name_raw);

        aaa_stack_push(stack, field);

        aaa_string_dec_ref(field_name);
        aaa_struct_dec_ref(s);
    }

    fn field_update(&mut self) {
        struct aaa_variable *new_value = aaa_stack_pop(stack);
        struct aaa_string *field_name = aaa_stack_pop_str(stack);
        struct aaa_struct *s = aaa_stack_pop_struct(stack);

        const char *field_name_raw = aaa_string_raw(field_name);
        aaa_struct_set_field(s, field_name_raw, new_value);

        aaa_variable_dec_ref(new_value);
        aaa_string_dec_ref(field_name);
        aaa_struct_dec_ref(s);
    }

    fn fsync(&mut self) {
        int fd = aaa_stack_pop_int(stack);

        if (fsync(fd) == -1) {
            aaa_stack_push_bool(stack, false);
        }

        aaa_stack_push_bool(stack, true);
    }

    fn environ(&mut self) {
        struct aaa_map *map = aaa_map_new();

        struct aaa_string *equals_char = aaa_string_new("=", false);

        for (char **env_item = environ; *env_item; env_item++) {
            struct aaa_string *item = aaa_string_new(*env_item, false);

            size_t equals_char_offset;
            bool success;
            aaa_string_find(item, equals_char, &equals_char_offset, &success);
            assert(success);

            size_t item_length = aaa_string_len(item);

            struct aaa_string *key_str =
                aaa_string_substr(item, 0, equals_char_offset, &success);
            assert(success);

            struct aaa_string *value_str = aaa_string_substr(
                item, equals_char_offset + 1, item_length, &success);
            assert(success);

            struct aaa_variable *key = aaa_variable_new_str(key_str);
            struct aaa_variable *value = aaa_variable_new_str(value_str);

            aaa_map_set(map, key, value);

            aaa_variable_dec_ref(key);
            aaa_variable_dec_ref(value);
            aaa_string_dec_ref(item);
        }

        aaa_string_dec_ref(equals_char);
        aaa_stack_push_map(stack, map);
    }

    fn execve(&mut self) {
        struct aaa_map *env_map = aaa_stack_pop_map(stack);
        struct aaa_vector *argv_vec = aaa_stack_pop_vec(stack);
        struct aaa_string *path_str = aaa_stack_pop_str(stack);

        size_t argv_length = aaa_vector_size(argv_vec);
        size_t env_length = aaa_map_size(env_map);

        const char *path = aaa_string_raw(path_str);
        char **argv = malloc((argv_length + 1) * sizeof(*argv));

        struct aaa_vector_iter *argv_vec_iter = aaa_vector_iter_new(argv_vec);
        struct aaa_variable *argv_item_var = NULL;
        size_t i = 0;

        while (aaa_vector_iter_next(argv_vec_iter, &argv_item_var)) {
            struct aaa_string *argv_item = aaa_variable_get_str(argv_item_var);

            const char *argv_item_raw = aaa_string_raw(argv_item);
            size_t argv_item_length = aaa_string_len(argv_item);

            argv[i] = malloc((argv_item_length + 1) * sizeof(char));
            strcpy(argv[i], argv_item_raw);
            i++;
        }

        aaa_vector_iter_dec_ref(argv_vec_iter);

        argv[argv_length] = NULL;

        char **env = malloc((env_length + 1) * sizeof(*env));

        struct aaa_map_iter *env_iter = aaa_map_iter_new(env_map);

        struct aaa_variable *env_key_var = NULL;
        struct aaa_variable *env_value_var = NULL;

        size_t env_offset = 0;
        while (aaa_map_iter_next(env_iter, &env_key_var, &env_value_var)) {
            struct aaa_string *env_key = aaa_variable_get_str(env_key_var);
            struct aaa_string *env_value = aaa_variable_get_str(env_value_var);

            size_t key_length = aaa_string_len(env_key);
            size_t value_length = aaa_string_len(env_value);

            char *env_item = malloc(key_length + value_length + 2 * sizeof(char));
            sprintf(env_item, "%s=%s", aaa_string_raw(env_key),
                    aaa_string_raw(env_value));

            env[env_offset] = env_item;
            env_offset++;
        }

        env[env_length] = NULL;

        execve(path, argv, env);

        // NOTE: execve() only returns when it fails.

        for (i = 0; i < argv_length; i++) {
            free(argv[i]);
        }

        free(argv);

        for (i = 0; i < env_length; i++) {
            free(env[i]);
        }

        free(env);

        aaa_map_iter_dec_ref(env_iter);

        aaa_string_dec_ref(path_str);
        aaa_vector_dec_ref(argv_vec);
        aaa_map_dec_ref(env_map);

        aaa_stack_push_bool(stack, false);
    }

    fn fork(&mut self) {
        int pid = fork();

        aaa_stack_push_int(stack, pid);
    }

    fn waitpid(&mut self) {
        int options = aaa_stack_pop_int(stack);
        int pid = aaa_stack_pop_int(stack);

        int status_raw;
        int changed_pid = waitpid(pid, &status_raw, options);

        if (changed_pid == 0) {
            aaa_stack_push_int(stack, 0);
            aaa_stack_push_int(stack, 0);
            aaa_stack_push_bool(stack, false);
            aaa_stack_push_bool(stack, false);
        } else {
            int status;
            bool child_exited;

            if (WIFEXITED(status_raw)) {
                child_exited = true;
                status = WEXITSTATUS(status_raw);
            } else {
                child_exited = false;
                status = 0;
            }

            aaa_stack_push_int(stack, changed_pid);
            aaa_stack_push_int(stack, status);
            aaa_stack_push_bool(stack, child_exited);
            aaa_stack_push_bool(stack, true);
        }
    }

    fn getcwd(&mut self) {
        size_t buff_size = PATH_MAX;
        char *buff = malloc(buff_size);

        if (getcwd(buff, buff_size) == NULL) {
            fprintf(stderr, "getcwd() failed\n");
            abort();
        }

        aaa_stack_push_str_raw(stack, buff, true);
    }

    fn chdir(&mut self) {
        struct aaa_string *path = aaa_stack_pop_str(stack);
        const char *path_raw = aaa_string_raw(path);

        if (chdir(path_raw) == 0) {
            aaa_stack_push_bool(stack, true);
        } else {
            aaa_stack_push_bool(stack, false);
        }

        aaa_string_dec_ref(path);
    }

    fn close(&mut self) {
        int fd = aaa_stack_pop_int(stack);

        if (close(fd) == 0) {
            aaa_stack_push_bool(stack, true);
        } else {
            aaa_stack_push_bool(stack, false);
        }
    }

    fn getpid(&mut self) {
        int pid = getpid();

        aaa_stack_push_int(stack, pid);
    }

    fn getppid(&mut self) {
        int ppid = getppid();

        aaa_stack_push_int(stack, ppid);
    }

    fn getenv(&mut self) {
        struct aaa_string *name = aaa_stack_pop_str(stack);
        const char *name_raw = aaa_string_raw(name);

        const char *value = getenv(name_raw);

        if (value) {
            aaa_stack_push_str_raw(stack, value, false);
            aaa_stack_push_bool(stack, true);
        } else {
            aaa_stack_push_str_raw(stack, "", false);
            aaa_stack_push_bool(stack, false);
        }

        aaa_string_dec_ref(name);
    }

    fn gettimeofday(&mut self) {
        struct timeval tv;

        if (gettimeofday(&tv, NULL) != 0) {
            fprintf(stderr, "gettimeofday() failed\n");
            abort();
        }

        aaa_stack_push_int(stack, (int)tv.tv_sec);
        aaa_stack_push_int(stack, (int)tv.tv_usec);
    }

    fn open(&mut self) {
        int mode = aaa_stack_pop_int(stack);
        int flags = aaa_stack_pop_int(stack);
        struct aaa_string *path = aaa_stack_pop_str(stack);

        const char *path_raw = aaa_string_raw(path);

        int fd = open(path_raw, flags, mode);

        if (fd == -1) {
            aaa_stack_push_int(stack, 0);
            aaa_stack_push_bool(stack, false);
        } else {
            aaa_stack_push_int(stack, fd);
            aaa_stack_push_bool(stack, true);
        }

        aaa_string_dec_ref(path);
    }

    fn setenv(&mut self) {
        struct aaa_string *value = aaa_stack_pop_str(stack);
        struct aaa_string *name = aaa_stack_pop_str(stack);

        const char *value_raw = aaa_string_raw(value);
        const char *name_raw = aaa_string_raw(name);

        if (setenv(name_raw, value_raw, 1) == -1) {
            fprintf(stderr, "setenv() failed\n");
            abort();
        }

        aaa_string_dec_ref(value);
        aaa_string_dec_ref(name);
    }

    fn time(&mut self) {
        time_t timestamp = time(NULL);

        aaa_stack_push_int(stack, (int)timestamp);
    }

    fn unlink(&mut self) {
        struct aaa_string *path = aaa_stack_pop_str(stack);

        const char *path_raw = aaa_string_raw(path);

        if (unlink(path_raw) == 0) {
            aaa_stack_push_bool(stack, true);
        } else {
            aaa_stack_push_bool(stack, false);
        }

        aaa_string_dec_ref(path);
    }

    fn unsetenv(&mut self) {
        struct aaa_string *name = aaa_stack_pop_str(stack);

        const char *name_raw = aaa_string_raw(name);

        if (unsetenv(name_raw) == -1) {
            fprintf(stderr, "unsetenv() failed\n");
            abort();
        }

        aaa_string_dec_ref(name);
    }

    fn vec_iter(&mut self) {
        struct aaa_vector *vec = aaa_stack_pop_vec(stack);
        struct aaa_vector_iter *iter = aaa_vector_iter_new(vec);
        struct aaa_variable *var = aaa_variable_new_vector_iter(iter);

        aaa_stack_push(stack, var);

        aaa_vector_dec_ref(vec);
    }

    fn vec_iter_next(&mut self) {
        struct aaa_variable *top = aaa_stack_pop(stack);
        struct aaa_vector_iter *iter = aaa_variable_get_vector_iter(top);

        aaa_vector_iter_inc_ref(iter);
        aaa_variable_dec_ref(top);

        struct aaa_variable *item = NULL;
        bool has_next = aaa_vector_iter_next(iter, &item);

        aaa_stack_push(stack, item);
        aaa_stack_push_bool(stack, has_next);

        aaa_vector_iter_dec_ref(iter);
    }

    fn map_iter(&mut self) {
        struct aaa_map *map = aaa_stack_pop_map(stack);

        struct aaa_map_iter *iter = aaa_map_iter_new(map);
        struct aaa_variable *var = aaa_variable_new_map_iter(iter);

        aaa_stack_push(stack, var);

        aaa_map_dec_ref(map);
    }

    fn map_iter_next(&mut self) {
        struct aaa_variable *top = aaa_stack_pop(stack);
        struct aaa_map_iter *iter = aaa_variable_get_map_iter(top);

        aaa_map_iter_inc_ref(iter);
        aaa_variable_dec_ref(top);

        struct aaa_variable *key = NULL;
        struct aaa_variable *value = NULL;
        bool has_next = aaa_map_iter_next(iter, &key, &value);

        aaa_stack_push(stack, key);
        aaa_stack_push(stack, value);
        aaa_stack_push_bool(stack, has_next);

        aaa_map_iter_dec_ref(iter);
    }

    fn set_add(&mut self) {
        struct aaa_variable *item = aaa_stack_pop(stack);
        struct aaa_map *set = aaa_stack_pop_map(stack);

        aaa_map_set(set, item, NULL);

        aaa_map_dec_ref(set);
        aaa_variable_dec_ref(item);
    }

    fn set_clear(&mut self) {
        struct aaa_map *set = aaa_stack_pop_map(stack);

        aaa_map_clear(set);

        aaa_map_dec_ref(set);
    }

    fn set_copy(&mut self) {
        struct aaa_map *set = aaa_stack_pop_map(stack);

        struct aaa_map *copy = aaa_map_copy(set);

        aaa_stack_push_map(stack, copy);

        aaa_map_dec_ref(set);
    }

    fn set_empty(&mut self) {
        struct aaa_map *set = aaa_stack_pop_map(stack);

        bool is_empty = aaa_map_empty(set);

        aaa_stack_push_bool(stack, is_empty);

        aaa_map_dec_ref(set);
    }

    fn set_has(&mut self) {
        struct aaa_variable *item = aaa_stack_pop(stack);
        struct aaa_map *set = aaa_stack_pop_map(stack);

        bool has_key = aaa_map_has_key(set, item);

        aaa_stack_push_bool(stack, has_key);

        aaa_map_dec_ref(set);
        aaa_variable_dec_ref(item);
    }

    fn set_iter(&mut self) { aaa_stack_map_iter(stack); }

    fn set_remove(&mut self) {
        struct aaa_variable *item = aaa_stack_pop(stack);
        struct aaa_map *set = aaa_stack_pop_map(stack);

        aaa_map_pop(set, item);

        aaa_variable_dec_ref(item);
        aaa_map_dec_ref(set);
    }

    fn set_size(&mut self) {
        return aaa_stack_map_size(stack);
    }

    fn set_iter_next(&mut self) {
        struct aaa_variable *top = aaa_stack_pop(stack);
        struct aaa_map_iter *iter = aaa_variable_get_map_iter(top);

        aaa_map_iter_inc_ref(iter);
        aaa_variable_dec_ref(top);

        struct aaa_variable *key = NULL;
        struct aaa_variable *value = NULL;
        bool has_next = aaa_map_iter_next(iter, &key, &value);

        aaa_stack_push(stack, key);
        aaa_stack_push_bool(stack, has_next);

        aaa_map_iter_dec_ref(iter);
    }

    fn push_set_empty(&mut self) {
        struct aaa_map *set = aaa_set_new();
        aaa_stack_push_set(stack, set);
    }

    void aaa_stack_variable_assign(struct aaa_stack *stack,
                                   struct aaa_variable *var) {
        struct aaa_variable *popped = aaa_stack_pop(stack);
        aaa_variable_assign(var, popped);
        aaa_variable_dec_ref(popped);
    }

    fn copy(&mut self) {
        struct aaa_variable *top = aaa_stack_top(stack);
        struct aaa_variable *copy = aaa_variable_copy(top);

        aaa_stack_push(stack, copy);
    }

    fn make_const(&mut self) {
    } */
}
