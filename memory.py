import asyncio
import os
import time

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_ollama import OllamaEmbeddings

# Initialize Local Embeddings (Nomic is great for code/context)
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Initialize ChromaDB
# Folder 'local_rag_db' stores your persistent preferences and solved code
vector_store = Chroma(
    collection_name="developer_memory",
    embedding_function=embeddings,
    persist_directory="./local_rag_db",
)


async def add_to_long_term_memory(text: str, metadata: dict = None):
    """Saves preferences, constraints, or successful code to Chroma."""
    meta = metadata if metadata is not None else {}
    meta["timestamp"] = time.time()
    vector_store.add_texts(texts=[text], metadatas=[meta])


async def get_sparse(query: str, k: int):
    all_docs_data = vector_store.get()
    all_texts = all_docs_data["documents"]
    all_metadatas = all_docs_data["metadatas"]

    if not all_texts:
        return []

    # Initialize BM25 with existing documents
    # For performance, consider pre-initializing this outside the function
    bm25_retriever = BM25Retriever.from_texts(all_texts, metadatas=all_metadatas)
    bm25_retriever.k = k
    return await asyncio.to_thread(bm25_retriever.invoke, query)


def format_docs(docs):
    sorted_docs = sorted(
        docs, key=lambda d: d.metadata.get("timestamp", 0), reverse=True
    )
    return (
        "\n".join([f"- {d.page_content}" for d in sorted_docs])
        if sorted_docs
        else "No matches."
    )


async def query_long_term_memory(query: str, k: int = 5) -> str:
    """Searches past context to inform the current task."""
    print(f"Searching db for:'''{query}''', with k={k}")
    dense_task = asyncio.to_thread(vector_store.similarity_search, query, k=k)
    dense_results, sparse_results = await asyncio.gather(dense_task, get_sparse(query, k))
    
    if not dense_results and not sparse_results:
        return "No specific past context found."
        
    formatted_context = (
        f"### SEMANTIC CONTEXT (Conceptual Matches):\n{format_docs(dense_results)}\n\n"
        f"### KEYWORD CONTEXT (Exact Matches):\n{format_docs(sparse_results)}"
    )

    return formatted_context
