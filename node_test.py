from sandbox_node import Node as nd

node = nd()
result = node.execute_command("pip install requests")
print(result)
