import subprocess
import tempfile
import os
import sys
import logging
from typing import Dict, Any
from pathlib import Path
from config.settings import settings

logger = logging.getLogger(__name__)

class PythonExecutor:
    """
    Sandboxed Python code executor for data analysis.
    Executes Python code in a restricted environment and captures output.
    """
    
    def __init__(self):
        self.timeout = 30  # seconds
        self.allowed_imports = [
            "pandas", "numpy", "matplotlib", "seaborn", 
            "scipy", "sklearn", "math", "statistics"
        ]
        
    def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code and return results.
        
        Args:
            code: Python code to execute
            
        Returns:
            Dict with 'output', 'error', 'artifacts' (e.g., plot paths)
        """
        if settings.features.mock_mode:
            return {
                "output": "Mock execution result: Mean = 42.5",
                "error": None,
                "artifacts": []
            }
        
        # Validate code (basic security check)
        if not self._is_safe(code):
            return {
                "output": "",
                "error": "Code contains disallowed operations",
                "artifacts": []
            }
        
        # Create temporary directory for artifacts
        with tempfile.TemporaryDirectory() as tmpdir:
            # Wrap code to capture output and save plots
            wrapped_code = self._wrap_code(code, tmpdir)
            
            # Write to temp file
            code_file = Path(tmpdir) / "exec.py"
            code_file.write_text(wrapped_code)
            
            try:
                # Execute in subprocess for isolation using current Python interpreter
                result = subprocess.run(
                    [sys.executable, str(code_file)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=tmpdir
                )
                
                # Collect generated artifacts (e.g., plots)
                artifacts = []
                for file in Path(tmpdir).glob("*.png"):
                    # Copy to persistent location
                    dest = Path("/tmp") / file.name
                    dest.write_bytes(file.read_bytes())
                    artifacts.append(str(dest))
                
                return {
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None,
                    "artifacts": artifacts
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "output": "",
                    "error": f"Execution timed out after {self.timeout}s",
                    "artifacts": []
                }
            except Exception as e:
                return {
                    "output": "",
                    "error": str(e),
                    "artifacts": []
                }
    
    def _is_safe(self, code: str) -> bool:
        """
        Basic security check for disallowed operations.
        """
        disallowed = ["import os", "import sys", "subprocess", "eval(", "exec(", "__import__"]
        for pattern in disallowed:
            if pattern in code:
                logger.warning(f"Disallowed pattern detected: {pattern}")
                return False
        return True
    
    def _wrap_code(self, code: str, output_dir: str) -> str:
        """
        Wrap user code to capture output and configure matplotlib.
        """
        # Only import matplotlib if it's used in the code
        has_matplotlib = "matplotlib" in code or "plt" in code
        
        if has_matplotlib:
            wrapper = f"""
import sys
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# User code
{code}

# Save any open figures
for i, fig in enumerate(plt.get_fignums()):
    plt.figure(fig)
    plt.savefig('{output_dir}/plot_{{i}}.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
"""
        else:
            wrapper = f"""
import sys

# User code
{code}
"""
        return wrapper
