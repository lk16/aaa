// TODO remove aaa-stdlib-user completely

use aaa_stdlib::stack::Stack;

fn main() {
    let mut stack = Stack::new();

    stack.push_int(34);
    stack.push_int(35);
    stack.plus();
    stack.print();

    stack.push_str("\n".to_owned());
    stack.print();

    something(&mut stack);
}

fn something(stack: &mut Stack) {
    stack.push_bool(true)
}
