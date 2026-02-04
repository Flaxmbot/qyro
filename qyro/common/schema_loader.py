import json
from .type_generator import NexusTypeGenerator
import os

class NexusSchemaLoader:
    def __init__(self):
        pass

    def process_schema(self, schema_block: str, output_dir="nexus_generated"):
        try:
            schema = json.loads(schema_block)
            generator = NexusTypeGenerator(schema)
            
            os.makedirs(output_dir, exist_ok=True)
            
            with open(os.path.join(output_dir, "nexus_types.h"), "w") as f:
                f.write(generator.generate_c_structs())
                
            with open(os.path.join(output_dir, "nexus_types.rs"), "w") as f:
                f.write(generator.generate_rust_structs())
                
            with open(os.path.join(output_dir, "GlobalState.java"), "w") as f:
                f.write(generator.generate_java_class())

            with open(os.path.join(output_dir, "types.ts"), "w") as f:
                f.write(generator.generate_ts_interface())
                
            print(f"[NEXUS] Schema processed. Types generated in {output_dir}/")
            return schema
            
        except json.JSONDecodeError as e:
            print(f"[NEXUS] Error parsing schema block: {e}")
            return None
