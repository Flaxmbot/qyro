import re

class NexusParser:
    def __init__(self):
        self.blocks = {
            'py': [],
            'js': [],
            'rs': [],
            'c': [],
            'java': [],
            'node': [],
            'ts': [],
            'go': [],
            'web': [],
            'schema': [],
            'react': [],
            'nextjs': [],
        }
        self.named_blocks = {}

    def parse_file(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            # Pass the directory of the file as base_path
            import os
            base_path = os.path.dirname(filepath) or "."
            self.parse_string(content, base_path=base_path)
        except FileNotFoundError:
            print(f"[QYRO] Error: File {filepath} not found.")

    def parse_string(self, content: str, base_path="."):
        # Import handling: >>>import "path/to/file.qyro"
        import_pattern = re.compile(r'^>>>import\s+"([^"]+)"', re.MULTILINE)
        for match in import_pattern.finditer(content):
            rel_path = match.group(1)
            import os
            # Resolve relative to base_path
            full_path = os.path.join(base_path, rel_path)
            print(f"[QYRO] Importing {full_path}...")
            self.parse_file(full_path)

        # Split by block markers: >>>HEADER
        # Captures the entire header line after >>>
        parts = re.split(r'(?m)^>>>((?:(?!\n).)*)$', content)
        
        if len(parts) < 2:
            return 
            
        for i in range(1, len(parts), 2):
            header = parts[i].strip()
            block_content = parts[i+1].strip()
            
            # Parse header: type:name [deps]
            # Regex: TYPE (:NAME)? (\s* [DEPS])?
            header_match = re.match(r'^([^:\s]+)(?::([^:\s\[]+))?\s*(?:\[(.*?)\])?', header)
            
            if not header_match:
                # Fallback for simple cases if regex fails (unlikely)
                block_type = header.lower()
                block_name = f"module_{i}"
                deps = []
            else:
                block_type = header_match.group(1).lower()
                block_name = header_match.group(2) if header_match.group(2) else f"module_{i}"
                deps_str = header_match.group(3)
                deps = [d.strip() for d in deps_str.split(',')] if deps_str else []

            if block_type == 'import': 
                continue

            # Store in legacy string list (Backward Compatibility)
            if block_type not in self.blocks:
                self.blocks[block_type] = []
            self.blocks[block_type].append(block_content)
            
            # Store in unified named blocks list (For Build System)
            if block_type not in self.named_blocks:
                self.named_blocks[block_type] = []
            
            self.named_blocks[block_type].append({
                "name": block_name,
                "content": block_content,
                "original_type": header,
                "dependencies": deps
            })

    def get_blocks(self, block_type: str):
        return self.blocks.get(block_type, [])

    def get_named_blocks(self):
        """Return all blocks with their metadata (name, type)."""
        return getattr(self, 'named_blocks', {})


# Qyro compatibility alias
QyroParser = NexusParser
