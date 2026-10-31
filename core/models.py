import os
import warnings
from typing import List

warnings.filterwarnings("ignore", message="coroutine 'ClientResponse.json' was never awaited")

from dotenv import load_dotenv
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from tools import coding_tools, non_coding_tools

load_dotenv()


client = genai.Client()

# Make sure your GOOGLE_API_KEY is set in your environment variables
base_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.5)

from tools.coding_tools import (
    route_to_coding,
    route_to_thinking,
    route_to_coder_thinking,
    route_back_to_thinking,
    git_status,
    git_log,
    search_in_project,
    read_file_content,
    write_project_memory,
    write_tasks,
    append_project_timeline,
    route_to_research,
    route_to_orchestrator,
)
from tools.coding_tools import web_search, curl_fetch

# Tools available to the thinking/planning node:
# Read-only + memory/task writing + search + routing to coder_thinking (NOT directly to coding)
thinking_tools = [
    route_to_coder_thinking,
    git_status,
    git_log,
    search_in_project,
    read_file_content,
    write_project_memory,
    write_tasks,
    append_project_timeline,
    web_search,
]

# Tools available to the coder thinking node:
# Read-only + routing to coding or back to thinking
coder_thinking_tools = [
    route_to_coding,
    route_back_to_thinking,
    git_status,
    git_log,
    search_in_project,
    read_file_content,
    write_project_memory,
    write_tasks,
    append_project_timeline,
    web_search,
]

orchestrator_read_tools = [
    route_to_thinking,
    route_to_research,
]

orchestrator_llm = base_llm.bind_tools(non_coding_tools)
orchestrator_project_llm = base_llm.bind_tools(
    orchestrator_read_tools + non_coding_tools
)
thinking_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", temperature=0.5
).bind_tools(thinking_tools)
coder_thinking_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", temperature=0.5
).bind_tools(coder_thinking_tools)
coding_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", temperature=0.5
).bind_tools(coding_tools)

research_tools = [
    web_search,
    curl_fetch,
    search_in_project,
    read_file_content,
    route_to_orchestrator,
]

research_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", temperature=0.5
).bind_tools(research_tools)

def _build_gemini_llm(api_keys, model_name, temperature, bind_tools_list=None, structured_output=None):
    if not api_keys:
        m = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, max_retries=1)
        if bind_tools_list: m = m.bind_tools(bind_tools_list)
        if structured_output: m = m.with_structured_output(structured_output)
        return m
    
    models = []
    for key in api_keys:
        m = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=key, max_retries=1)
        if bind_tools_list: m = m.bind_tools(bind_tools_list)
        if structured_output: m = m.with_structured_output(structured_output)
        models.append(m)
        
    if len(models) > 1:
        return models[0].with_fallbacks(models[1:])
    return models[0]

def update_gemini_models(api_keys, model_name: str):
    global base_llm, orchestrator_llm, orchestrator_project_llm, thinking_llm, coder_thinking_llm, coding_llm, welcome_message_llm, memory_update_llm, client
    
    if isinstance(api_keys, str):
        api_keys = [api_keys]
        
    if api_keys:
        os.environ["GOOGLE_API_KEY"] = api_keys[0]
        client = genai.Client(api_key=api_keys[0])
    
    base_llm = _build_gemini_llm(api_keys, model_name, 0.5)
    orchestrator_llm = _build_gemini_llm(api_keys, model_name, 0.5, bind_tools_list=non_coding_tools)
    orchestrator_project_llm = _build_gemini_llm(api_keys, model_name, 0.5, bind_tools_list=orchestrator_read_tools + non_coding_tools)
    thinking_llm = _build_gemini_llm(api_keys, model_name, 0.5, bind_tools_list=thinking_tools)
    coder_thinking_llm = _build_gemini_llm(api_keys, model_name, 0.5, bind_tools_list=coder_thinking_tools)
    coding_llm = _build_gemini_llm(api_keys, model_name, 0.5, bind_tools_list=coding_tools)
    welcome_message_llm = _build_gemini_llm(api_keys, model_name, 0.7)
    memory_update_llm = _build_gemini_llm(api_keys, model_name, 0.5, structured_output=MemoryExtractionResult)


def _build_openrouter_llm(api_keys, model_name, temperature, bind_tools_list=None, structured_output=None):
    if not api_keys:
        m = ChatOpenAI(
            model=model_name, temperature=temperature, 
            base_url="https://openrouter.ai/api/v1", stream_chunk_timeout=None, max_retries=1
        )
        if bind_tools_list: m = m.bind_tools(bind_tools_list)
        if structured_output: m = m.with_structured_output(structured_output)
        return m
    
    models = []
    for key in api_keys:
        m = ChatOpenAI(
            model=model_name, temperature=temperature, api_key=key,
            base_url="https://openrouter.ai/api/v1", stream_chunk_timeout=None, max_retries=1
        )
        if bind_tools_list: m = m.bind_tools(bind_tools_list)
        if structured_output: m = m.with_structured_output(structured_output)
        models.append(m)
        
    if len(models) > 1:
        return models[0].with_fallbacks(models[1:])
    return models[0]


def update_openrouter_models(api_keys, model_name: str):
    global base_llm, orchestrator_llm, orchestrator_project_llm, thinking_llm, coder_thinking_llm, coding_llm, welcome_message_llm, memory_update_llm, client
    
    if isinstance(api_keys, str):
        api_keys = [api_keys]
        
    if api_keys:
        os.environ["OPENROUTER_API_KEY"] = api_keys[0]
        client = None
    
    base_llm = _build_openrouter_llm(api_keys, model_name, 0.5)
    orchestrator_llm = _build_openrouter_llm(api_keys, model_name, 0.5, bind_tools_list=non_coding_tools)
    orchestrator_project_llm = _build_openrouter_llm(api_keys, model_name, 0.5, bind_tools_list=orchestrator_read_tools + non_coding_tools)
    thinking_llm = _build_openrouter_llm(api_keys, model_name, 0.5, bind_tools_list=thinking_tools)
    coder_thinking_llm = _build_openrouter_llm(api_keys, model_name, 0.5, bind_tools_list=coder_thinking_tools)
    coding_llm = _build_openrouter_llm(api_keys, model_name, 0.5, bind_tools_list=coding_tools)
    welcome_message_llm = _build_openrouter_llm(api_keys, model_name, 0.7)
    memory_update_llm = _build_openrouter_llm(api_keys, model_name, 0.5, structured_output=MemoryExtractionResult)


def _build_groq_llm(api_key, model_name, temperature, bind_tools_list=None, structured_output=None):
    """Groq uses OpenAI-compatible API — single key, no rotation needed."""
    m = ChatOpenAI(
        model=model_name, temperature=temperature, api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        stream_chunk_timeout=None, max_retries=2
    )
    if bind_tools_list: m = m.bind_tools(bind_tools_list)
    if structured_output: m = m.with_structured_output(structured_output)
    return m


def update_groq_models(api_key: str, model_name: str):
    global base_llm, orchestrator_llm, orchestrator_project_llm, thinking_llm
    global coder_thinking_llm, coding_llm, welcome_message_llm, memory_update_llm, client
    global research_llm
    
    os.environ["GROQ_API_KEY"] = api_key
    client = None  # No Gemini client for Groq
    
    base_llm = _build_groq_llm(api_key, model_name, 0.5)
    orchestrator_llm = _build_groq_llm(api_key, model_name, 0.5, bind_tools_list=non_coding_tools)
    orchestrator_project_llm = _build_groq_llm(api_key, model_name, 0.5, bind_tools_list=orchestrator_read_tools + non_coding_tools)
    thinking_llm = _build_groq_llm(api_key, model_name, 0.5, bind_tools_list=thinking_tools)
    coder_thinking_llm = _build_groq_llm(api_key, model_name, 0.5, bind_tools_list=coder_thinking_tools)
    coding_llm = _build_groq_llm(api_key, model_name, 0.5, bind_tools_list=coding_tools)
    research_llm = _build_groq_llm(api_key, model_name, 0.5, bind_tools_list=research_tools)
    welcome_message_llm = _build_groq_llm(api_key, model_name, 0.7)
    memory_update_llm = _build_groq_llm(api_key, model_name, 0.5, structured_output=MemoryExtractionResult)


def update_ollama_models(base_url: str, model_name: str):
    global base_llm, orchestrator_llm, orchestrator_project_llm, thinking_llm
    global coder_thinking_llm, coding_llm, welcome_message_llm, memory_update_llm
    global fast_llm, title_generator_llm, client, research_llm
    
    client = None
    
    def _build(model, temp, tools_list=None, structured=None):
        m = ChatOllama(model=model, temperature=temp, base_url=base_url)
        if tools_list: m = m.bind_tools(tools_list)
        if structured: m = m.with_structured_output(structured)
        return m
    
    base_llm = _build(model_name, 0.5)
    orchestrator_llm = _build(model_name, 0.5, tools_list=non_coding_tools)
    orchestrator_project_llm = _build(model_name, 0.5, tools_list=orchestrator_read_tools + non_coding_tools)
    thinking_llm = _build(model_name, 0.5, tools_list=thinking_tools)
    coder_thinking_llm = _build(model_name, 0.5, tools_list=coder_thinking_tools)
    coding_llm = _build(model_name, 0.5, tools_list=coding_tools)
    research_llm = _build(model_name, 0.5, tools_list=research_tools)
    welcome_message_llm = _build(model_name, 0.7)
    memory_update_llm = _build(model_name, 0.5, structured=MemoryExtractionResult)
    fast_llm = _build(model_name, 0.5)
    title_generator_llm = ChatOllama(model=model_name, temperature=0.0, num_predict=15, base_url=base_url)


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
