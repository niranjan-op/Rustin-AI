from sandbox_node import Node as nd

node = nd()
result = node.not_starting_server("""python -c "import os; print(os.getcwd())" """)
print(result)
