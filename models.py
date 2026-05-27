import os

from langchain_ollama import ChatOllama

from tools import tools

fast_llm = ChatOllama(model="llama3.2:1b", temperature=0.5, base_url="http://127.0.0.1:11434")
orchestrator_llm = ChatOllama(model="qwen3.5:4b", temperature=0.5, base_url="http://127.0.0.1:11434")
memory_update_llm = ChatOllama(model="llama3.2:1b", temperature=0.5, base_url="http://127.0.0.1:11434")

