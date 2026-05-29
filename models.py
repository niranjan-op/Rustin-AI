import os

from dotenv import load_dotenv
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from tools import tools

load_dotenv()


client = genai.Client()

# Make sure your GOOGLE_API_KEY is set in your environment variables
orchestrator_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", temperature=0.5
).bind_tools(tools)

fast_llm = ChatOllama(
    model="llama3.2:1b", temperature=0.5, base_url="http://127.0.0.1:11434"
)
# orchestrator_llm = ChatOllama(model="qwen3.5:4b", temperature=0.5, base_url="http://127.0.0.1:11434").bind_tools(tools)
memory_update_llm = ChatOllama(
    model="llama3.2:1b", temperature=0.5, base_url="http://127.0.0.1:11434"
)
