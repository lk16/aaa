// TODO remove aaa-stdlib-user completely

use aaa_stdlib::stack::Stack;

fn main() {
    let mut stack = Stack::new();

    stack.push_int(34);
    stack.push_int(35);
    stack.plus();
    stack.print_top();

    stack.push_str("\n".to_owned());
    stack.print_top();
}
