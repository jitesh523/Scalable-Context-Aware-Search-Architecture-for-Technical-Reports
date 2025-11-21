import pytest
from src.tools.python_executor import PythonExecutor
from config.settings import settings

def test_python_executor_mock_mode():
    """Test Python executor in mock mode."""
    settings.features.mock_mode = True
    executor = PythonExecutor()
    
    result = executor.execute("print('Hello')")
    assert result["output"] == "Mock execution result: Mean = 42.5"
    assert result["error"] is None

def test_python_executor_simple_code():
    """Test executing simple Python code."""
    settings.features.mock_mode = False
    executor = PythonExecutor()
    
    code = """
x = 10
y = 20
print(f"Sum: {x + y}")
"""
    
    result = executor.execute(code)
    print(f"Output: {result['output']}")
    print(f"Error: {result['error']}")
    assert "Sum: 30" in result["output"]
    assert result["error"] is None

def test_python_executor_disallowed_code():
    """Test that disallowed code is rejected."""
    settings.features.mock_mode = False
    executor = PythonExecutor()
    
    code = "import os; os.system('ls')"
    
    result = executor.execute(code)
    assert result["error"] == "Code contains disallowed operations"

@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("matplotlib"),
    reason="matplotlib not installed"
)
def test_python_executor_with_plot():
    """Test code that generates a plot."""
    settings.features.mock_mode = False
    executor = PythonExecutor()
    
    code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)
plt.title("Sine Wave")
"""
    
    result = executor.execute(code)
    assert result["error"] is None
    assert len(result["artifacts"]) > 0  # Should have saved a plot
