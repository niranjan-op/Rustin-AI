"""
Manual test: Verify the Node.js sandbox server can execute a command.
Run from the project root: python tests/node_test.py
"""
from sandbox.node_sandbox import Node as nd

node = nd()
result = node.not_starting_server("""python -c "import os; print(os.getcwd())" """)
print(result)
