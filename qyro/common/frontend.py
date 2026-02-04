"""
Nexus Frontend Compiler
Handles compilation and setup for frontend frameworks (React, Next.js).
"""

import os
import shutil
from typing import Dict, Any, List
from dataclasses import dataclass
from .logging import get_logger

logger = get_logger("nexus.frontend")

@dataclass
class FrontendConfig:
    framework: str = "react"  # 'react' or 'nextjs'
    port: int = 3000

class FrontendCompiler:
    def __init__(self, output_dir: str = "nexus_frontend"):
        self.output_dir = output_dir

    def compile_react(self, code: str, config: FrontendConfig) -> Dict[str, Any]:
        """
        Compile React code block.
        Since we're using Vite, "compilation" mainly means saving the file 
        to the correct location for Vite to pick up.
        """
        # Ensure output directory exists (created by orchestrator, but just in case)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        src_dir = os.path.join(self.output_dir, "src")
        if not os.path.exists(src_dir):
            os.makedirs(src_dir)

        # Save the component code
        # We assume the code block contains the full component definition
        # typically matching what goes into NexusComponent.tsx
        component_path = os.path.join(src_dir, "NexusComponent.tsx")
        
        # Add necessary imports if missing (simple heuristic)
        final_code = code
        if "import React" not in code and "import { useState" not in code:
             final_code = "import React, { useState, useEffect, useRef } from 'react';\n" + code

        # If the code doesn't export default, we might need to wrap or fix it.
        # But for now, we assume the user provides a valid component.
        # If it's a raw functional component without export, we might append the export.
        if "export default" not in final_code:
            final_code += "\n\nexport default NexusComponent;"

        try:
            with open(component_path, "w", encoding='utf-8') as f:
                f.write(final_code)
            
            logger.info(f"React component saved to {component_path}")
            
            return {
                "type": "react",
                "src": component_path,
                "framework": "vite"
            }
        except Exception as e:
            logger.error(f"Failed to save React component: {e}")
            raise e

    def compile_nextjs(self, code: str, config: FrontendConfig) -> Dict[str, Any]:
        """
        Compile Next.js code block.
        """
        # Similar logic for Next.js pages/components
        # For simplicity, we might map this to pages/index.tsx
        pass
