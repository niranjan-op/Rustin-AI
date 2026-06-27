import os
import sys

# Add the project root to sys.path so we can import from core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain_core.messages import HumanMessage, SystemMessage

from core.models import memory_update_llm
from core.prompts import memory_extract_llm_prompt

data = """
{
  "facts": [
    {
      "fact_key": "name",
      "fact_value": "Matt",
      "category": "user_profile"
    },
    {
      "fact_key": "university",
      "fact_value": "Stanford University",
      "category": "education"
    },
    {
      "fact_key": "profession",
      "fact_value": "Computer Engineer",
      "category": "demographic"
    },
    {
      "fact_key": "programming_languages",
      "fact_value": "C++ Python",
      "category": "interests"
    }
  ]
}"""


def test_memory_update_llm():
    print("Testing memory_update_llm...")
    print("Prompt template:")
    print("-" * 40)
    print(memory_extract_llm_prompt)
    print("-" * 40)

    existing_memories = [
        {"fact_key": "name", "fact_value": "Matt", "category": "user_profile"},
        {
            "fact_key": "profession",
            "fact_value": "Software Engineer",
            "category": "demographic",
        },
        {"fact_key": "location", "fact_value": "Bangalore", "category": "user_profile"},
        {
            "fact_key": "academic_focus",
            "fact_value": "Machine Learning",
            "category": "education",
        },
        {
            "fact_key": "os",
            "fact_value": "Lubuntu 24.04",
            "category": "technical_environment",
        },
        {
            "fact_key": "hardware_ram",
            "fact_value": "8GB",
            "category": "hardware_constraints",
        },
        {
            "fact_key": "hardware_cpu",
            "fact_value": "Intel i5",
            "category": "hardware_constraints",
        },
        {
            "fact_key": "primary_language",
            "fact_value": "Python",
            "category": "technical_skills",
        },
        {
            "fact_key": "secondary_language",
            "fact_value": "C++",
            "category": "technical_skills",
        },
        {
            "fact_key": "framework_preference",
            "fact_value": "PyTorch",
            "category": "technical_skills",
        },
        {"fact_key": "vector_db", "fact_value": "ChromaDB", "category": "architecture"},
        {
            "fact_key": "database_preference",
            "fact_value": "PostgreSQL",
            "category": "architecture",
        },
        {
            "fact_key": "ide",
            "fact_value": "VS Code",
            "category": "technical_environment",
        },
        {
            "fact_key": "active_project",
            "fact_value": "Graph-Neural-Scheduler",
            "category": "projects",
        },
        {
            "fact_key": "project_status",
            "fact_value": "Active development",
            "category": "projects",
        },
        {"fact_key": "hobby", "fact_value": "Powerlifting", "category": "interests"},
        {
            "fact_key": "study_topics",
            "fact_value": "Quantum Computing, Vedic Mathematics",
            "category": "interests",
        },
        {
            "fact_key": "work_style",
            "fact_value": "5 AM deep work",
            "category": "behavioral",
        },
        {
            "fact_key": "beverage_preference",
            "fact_value": "Espresso",
            "category": "lifestyle",
        },
        {
            "fact_key": "pet",
            "fact_value": "Node (cat), Byte (dog)",
            "category": "personal",
        },
        {"fact_key": "cloud_provider", "fact_value": "AWS", "category": "architecture"},
        {
            "fact_key": "primary_browser",
            "fact_value": "Firefox",
            "category": "technical_environment",
        },
        {
            "fact_key": "coding_standard",
            "fact_value": "PEP8",
            "category": "architecture",
        },
        {
            "fact_key": "learning_method",
            "fact_value": "Project-based learning",
            "category": "education",
        },
        {
            "fact_key": "music_preference",
            "fact_value": "Lo-fi beats",
            "category": "lifestyle",
        },
    ]
    user_input = """
    Man, this laptop is completely choking and throwing OOM errors whenever I try to
    run these dense embedding matrices locally. 8 gigs is just not cutting it anymore.
    I'm honestly thinking about ripping out ChromaDB entirely and spinning up Qdrant
    in a docker container to see if that handles memory swapping any better.

    On top of that, I haven't touched the Graph Scheduler stuff in weeks; I completely
    shelved it because this new traffic simulation playground using reinforcement
    learning is consuming every free hour I have. I've been living on green tea
    instead of coffee just to survive the 3 AM debugging marathons. Also, I'm seriously
    starting to look into Go, because Python's execution speed is just bottlenecks
    all the way down when rendering this simulation grid.
    """

    combined_input = (
        f"Existing memories:\n{existing_memories}\n\nUser input:\n{user_input}"
    )

    print("Combined Input to LLM:")
    print(combined_input)
    print("-" * 40)

    try:
        print("Invoking LLM and streaming response...")
        # memory_extract_llm_prompt requires the 'memories' variable because it has a MessagesPlaceholder
        chain = memory_extract_llm_prompt | memory_update_llm

        final_response = None
        for chunk in chain.stream({"memories": [HumanMessage(content=combined_input)]}):
            # If the output is wrapped in structured_output, chunks might be partial Pydantic dicts
            # If it's a standard message, chunk.content holds the text.
            if hasattr(chunk, "content"):
                print(chunk.content, end="", flush=True)
            else:
                print(chunk, flush=True)
            final_response = chunk

        print("\n" + "-" * 40)
        print("Final Output:")
        print(final_response)

    except Exception as e:
        print(f"An error occurred while invoking the LLM: {e}")
        print(
            "Make sure Ollama is running locally and the 'llama3.2:1b' model is downloaded."
        )


if __name__ == "__main__":
    test_memory_update_llm()
