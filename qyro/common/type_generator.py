import json
import ast

class QyroTypeGenerator:
    def __init__(self, schema_json):
        self.schema = json.loads(schema_json) if isinstance(schema_json, str) else schema_json

    def _infer_type_from_value(self, value):
        """Infer the appropriate type for a given value."""
        if isinstance(value, list):
            if len(value) > 0:
                element_type = self._infer_type_from_value(value[0])
                return f"list[{element_type}]"
            else:
                return "list[any]"
        elif isinstance(value, dict):
            return "dict"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "bool"
        else:
            return "any"

    def _get_c_type(self, value):
        """Get appropriate C type for a value."""
        if isinstance(value, list):
            if len(value) > 0:
                element_type = self._get_c_type(value[0])
                # For C, we'll use void* for generic list and handle serialization separately
                return "void*"  # Will be serialized as JSON string
            else:
                return "void*"
        elif isinstance(value, dict):
            return "void*"  # Will be serialized as JSON string
        elif isinstance(value, int):
            if -2147483648 <= value <= 2147483647:
                return "int"
            else:
                return "long long"
        elif isinstance(value, float):
            return "double"
        elif isinstance(value, str):
            return "char*"  # Dynamic string allocation instead of fixed size
        elif isinstance(value, bool):
            return "int"  # C doesn't have bool, use int
        else:
            return "void*"

    def _get_rust_type(self, value):
        """Get appropriate Rust type for a value."""
        if isinstance(value, list):
            if len(value) > 0:
                element_type = self._get_rust_type(value[0])
                return f"Vec<{element_type}>"
            else:
                return "Vec<any>"
        elif isinstance(value, dict):
            return "std::collections::HashMap<String, serde_json::Value>"
        elif isinstance(value, int):
            if -2147483648 <= value <= 2147483647:
                return "i32"
            else:
                return "i64"
        elif isinstance(value, float):
            return "f64"
        elif isinstance(value, str):
            return "String"
        elif isinstance(value, bool):
            return "bool"
        else:
            return "serde_json::Value"

    def _get_java_type(self, value):
        """Get appropriate Java type for a value."""
        if isinstance(value, list):
            if len(value) > 0:
                element_type = self._get_java_type(value[0])
                return f"java.util.List<{element_type}>"
            else:
                return "java.util.List<Object>"
        elif isinstance(value, dict):
            return "java.util.Map<String, Object>"
        elif isinstance(value, int):
            if -2147483648 <= value <= 2147483647:
                return "int"
            else:
                return "long"
        elif isinstance(value, float):
            return "double"
        elif isinstance(value, str):
            return "String"
        elif isinstance(value, bool):
            return "boolean"
        else:
            return "Object"

    def _get_ts_type(self, value):
        """Get appropriate TypeScript type for a value."""
        if isinstance(value, list):
            if len(value) > 0:
                element_type = self._get_ts_type(value[0])
                return f"{element_type}[]"
            else:
                return "any[]"
        elif isinstance(value, dict):
            return "{ [key: string]: any }"
        elif isinstance(value, int) or isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "boolean"
        else:
            return "any"

    def generate_c_structs(self):
        code = "#include <stdint.h>\n#include <stdlib.h>\n#include <string.h>\n\n"
        code += "// Note: Complex types (lists, dicts) are stored as JSON strings and require serialization/deserialization\n"
        code += "typedef struct {\n"
        for key, value in self.schema.items():
            c_type = self._get_c_type(value)
            if c_type == "char*":
                # For strings, we'll use char* instead of fixed-size arrays to avoid buffer overflows
                code += f"    {c_type} {key};  // Dynamically allocated string\n"
            else:
                code += f"    {c_type} {key};\n"
        code += "} GlobalState;\n\n"
        # Add helper functions for managing dynamic strings
        code += "// Helper functions for dynamic memory management\n"
        code += "void init_GlobalState(GlobalState* state) {\n"
        for key, value in self.schema.items():
            c_type = self._get_c_type(value)
            if c_type == "char*":
                code += f"    state->{key} = NULL;\n"
            elif "void*" in c_type:  # For lists and dicts
                code += f"    state->{key} = NULL;\n"
        code += "}\n\n"
        code += "void free_GlobalState(GlobalState* state) {\n"
        for key, value in self.schema.items():
            c_type = self._get_c_type(value)
            if c_type == "char*":
                code += f"    if (state->{key}) free(state->{key});\n"
            elif "void*" in c_type:  # For lists and dicts
                code += f"    if (state->{key}) free(state->{key});\n"
        code += "}\n"
        return code

    def generate_rust_structs(self):
        code = "use serde::{Serialize, Deserialize};\nuse std::collections::HashMap;\n\n"
        code += "#[derive(Serialize, Deserialize, Debug, Clone)]\npub struct GlobalState {\n"
        for key, value in self.schema.items():
            rust_type = self._get_rust_type(value)
            code += f"    pub {key}: {rust_type},\n"
        code += "}\n"
        return code

    def generate_java_class(self):
        code = "package nexus;\n\nimport java.util.*;\n\npublic class GlobalState {\n"
        for key, value in self.schema.items():
            java_type = self._get_java_type(value)
            code += f"    public {java_type} {key};\n"
        code += "}\n"
        return code

    def generate_ts_interface(self):
        code = "export interface GlobalState {\n"
        for key, value in self.schema.items():
            ts_type = self._get_ts_type(value)
            code += f"  {key}: {ts_type};\n"
        code += "}\n"
        return code
