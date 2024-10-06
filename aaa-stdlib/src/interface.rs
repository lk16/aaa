use crate::stack::InterfaceMappingType;

fn call_interface_function<T>(
    interface_mapping: &InterfaceMappingType<T>,
    interface_name: &str,
    function_name: &str,
) {
    let top = self.top();
    let top_type_id = top.type_id();

    let interface_name = format!("builtins:{}", interface_name);

    let first_key = &(interface_name.as_str(), top_type_id.as_str());

    let function = interface_mapping
        .get(first_key)
        .unwrap()
        .get(function_name)
        .unwrap();

    function(self);
}
