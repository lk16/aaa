use aaa_stdlib::stack::Stack;

fn main() {
    let mut stack = Stack::new();

    stack.push_int(69);
    stack.print_top();

    stack.push_str("\n".to_owned());
    stack.print_top();
}
