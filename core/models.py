import os
from typing import List

from dotenv import load_dotenv
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from tools import coding_tools, non_coding_tools

load_dotenv()


client = genai.Client()

# Make sure your GOOGLE_API_KEY is set in your environment variables
base_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.5)
# base_llm = ChatOllama(
#     model="llama3.2:3b", temperature=0.9, base_url="http://127.0.0.1:11434"
# )
from tools.coding_tools import (
    route_to_thinking,
    route_to_coding,
)

orchestrator_read_tools = [
    route_to_thinking,
]

orchestrator_llm = base_llm.bind_tools(non_coding_tools)
orchestrator_project_llm = base_llm.bind_tools(orchestrator_read_tools + non_coding_tools)
thinking_llm = base_llm.bind_tools([route_to_coding])
coding_llm = base_llm.bind_tools(coding_tools)

fast_llm = ChatOllama(
    model="llama3.2:1b", temperature=0.5, base_url="http://127.0.0.1:11434"
)
title_generator_llm = ChatOllama(
    model="llama3.2:1b",
    temperature=0.0,
    num_predict=15,
    base_url="http://127.0.0.1:11434",
)
welcome_message_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.7,
)


# orchestrator_llm = ChatOllama(model="qwen3.5:4b", temperature=0.5, base_url="http://127.0.0.1:11434").bind_tools(tools)
class AtomicFact(BaseModel):
    fact_key: str = Field(description="The key of the fact (e.g., name, university)")
    fact_value: str = Field(description="The value of the fact")
    category: str = Field(
        description="Category of the fact (e.g., user_profile, education)"
    )


class MemoryExtractionResult(BaseModel):
    facts: List[AtomicFact] = Field(
        description="List of extracted atomic facts from the user's input"
    )


memory_update_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", temperature=0.5
).with_structured_output(MemoryExtractionResult)
