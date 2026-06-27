import os
import sys

# Add the project root to sys.path so we can import from core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.tests.memory_update_llm import test_memory_update_llm

if __name__ == "__main__":
    test_memory_update_llm()
