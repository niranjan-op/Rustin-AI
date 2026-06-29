import json
import os as _os
import random
import sqlite3
import uuid

import chainlit as cl
from chainlit.context import context
from langchain_core.messages import AIMessage, HumanMessage

from agent.states import AgentState
from core.models import (
    memory_update_llm,
    orchestrator_llm,
    orchestrator_project_llm,
    welcome_message_llm,
    thinking_llm,
    coding_llm,
)
from core.prompts import (
    memory_extract_llm_prompt,
    orchestrator_llm_prompt,
    orchestrator_project_llm_prompt,
    welcome_message_prompt,
    thinking_node_prompt_text,
    coding_node_prompt_text,
)

_PROJECT_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

DB_PATH = _os.path.join(_PROJECT_ROOT, ".files", "test.db")
WELCOME_TXT_PATH = _os.path.join(_PROJECT_ROOT, "welcome.txt")
PUBLIC_WELCOME_TXT_PATH = _os.path.join(_PROJECT_ROOT, "public", "welcome.txt")
NUM_WELCOME_SLOTS = 15
PRIORITY_FACT_KEYS = {
    "project",
    "tech_stack",
    "architecture",
    "task",
    "building",
    "working",
}


def _build_personalized_message(fact_key: str, fact_value: str, name: str) -> str:
    """Build a context-aware check-in message from a single fact."""
    if any(k in fact_key for k in PRIORITY_FACT_KEYS):
        return f"Project {fact_value} progress?"
    elif "language" in fact_key or "skill" in fact_key:
        return f"Practicing {fact_value}?"
    elif "goal" in fact_key or "roadmap" in fact_key:
        return f"Progress on {fact_value}?"
    elif "interest" in fact_key or "hobby" in fact_key:
        return f"Exploring {fact_value}?"
    elif "location" in fact_key or "company" in fact_key:
        return f"How's {fact_value}?"
    elif "name" in fact_key:
        return f"Welcome back, {fact_value}!"
    else:
        return f"Any {fact_value} news?"


def _get_directory_tree(path, prefix=""):
    tree = ""
    if not _os.path.exists(path):
        return tree
    
    ignore_dirs = {".git", "__pycache__", "venv", ".venv", "node_modules", ".files", "build", "dist"}
    try:
        entries = sorted(_os.listdir(path))
    except Exception:
        return tree
        
    entries = [e for e in entries if e not in ignore_dirs]
    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        tree += prefix + connector + entry + "\n"
        
        full_path = _os.path.join(path, entry)
        if _os.path.isdir(full_path):
            extension = "    " if is_last else "│   "
            tree += _get_directory_tree(full_path, prefix=prefix + extension)
    return tree

async def thinking_node(state: AgentState):
    print("\n" + "="*50)
    print("🧠 [DEBUG] --- ENTERED THINKING NODE ---")
    print("="*50 + "\n")
    
    from langchain_core.prompts import ChatPromptTemplate
    
    messages = state.get("messages", [])
    
    # Build context injection from .model/ files
    context_parts = []
    project_structure = state.get("project_structure", "")
    if project_structure:
        context_parts.append(f"[PROJECT DIRECTORY STRUCTURE]:\n{project_structure}")
    project_memory = state.get("project_memory", "")
    if project_memory:
        context_parts.append(f"[PROJECT MEMORY]:\n{project_memory}")
    pending_tasks = state.get("pending_tasks", "")
    if pending_tasks:
        context_parts.append(f"[PENDING TASKS]:\n{pending_tasks}")
    project_timeline = state.get("project_timeline", "")
    if project_timeline:
        context_parts.append(f"[PROJECT TIMELINE]:\n{project_timeline}")
    learned = state.get("project_learned_features", [])
    if learned:
        context_parts.append(f"[LEARNED LESSONS]:\n{learned}")
    
    context_block = "\n\n".join(context_parts) if context_parts else ""
    system_prompt = thinking_node_prompt_text + ("\n\n" + context_block if context_block else "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | thinking_llm
    result = await chain.ainvoke({"messages": messages})
    
    # Only switch to coding phase when route_to_coding is called.
    # Other tool calls (search, read, write_tasks, etc.) loop back to thinking.
    target_phase = None
    if hasattr(result, "tool_calls") and result.tool_calls:
        for call in result.tool_calls:
            if call["name"] == "route_to_coding":
                target_phase = "coding"
                break
                
    if target_phase:
        return {"messages": [result], "response": result.content, "current_phase": target_phase}
    else:
        return {"messages": [result], "response": result.content}

async def coding_node(state: AgentState):
    print("\n" + "="*50)
    print("💻 [DEBUG] --- ENTERED CODING NODE ---")
    print("="*50 + "\n")
    
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.messages import SystemMessage
    
    messages = list(state.get("messages", []))
    
    # Build context injection from .model/ files
    context_parts = []
    project_structure = state.get("project_structure", "")
    if project_structure:
        context_parts.append(f"[PROJECT DIRECTORY STRUCTURE]:\n{project_structure}")
    project_memory = state.get("project_memory", "")
    if project_memory:
        context_parts.append(f"[PROJECT MEMORY]:\n{project_memory}")
    pending_tasks = state.get("pending_tasks", "")
    if pending_tasks:
        context_parts.append(f"[PENDING TASKS]:\n{pending_tasks}")
    
    context_block = "\n\n".join(context_parts) if context_parts else ""
    system_prompt = coding_node_prompt_text + ("\n\n" + context_block if context_block else "")
    
    # STATUS CHECK + BATCHING NUDGE: When re-invoked after tool results, inject a
    # dynamic status summary so the model knows exactly what it has already done,
    # and a firm reminder to batch all remaining independent tools.
    from langchain_core.messages import ToolMessage as _ToolMessage, AIMessage as _AIMessage
    
    # Collect all tool calls that have already been executed (have a corresponding ToolMessage)
    completed_tools = []
    for m in messages:
        if isinstance(m, _ToolMessage):
            completed_tools.append(m.name or "unknown_tool")
    
    has_recent_tool_results = any(
        isinstance(m, _ToolMessage) for m in messages[-10:]
    )
    
    if has_recent_tool_results:
        completed_summary = ", ".join(completed_tools) if completed_tools else "none yet"
        batching_nudge = SystemMessage(content=(
            f"[STATUS CHECK] Tools already executed so far in this task: [{completed_summary}]. "
            "Review the blueprint/plan from earlier in this conversation. "
            "Identify which phases/steps are DONE (their tools appear above) and which are REMAINING. "
            "Then execute ALL remaining independent tools for the next phase in THIS response. "
            "Do NOT repeat tools that are already done. "
            "Do NOT make a response with only 1 tool call — batch everything you can. "
            "If all phases are complete, call write_project_memory + append_project_timeline + write_tasks + git_add_and_commit together, then send a final summary."
        ))
        messages.append(batching_nudge)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | coding_llm
    result = await chain.ainvoke({"messages": messages})
    
    target_phase = None
    if hasattr(result, "tool_calls") and result.tool_calls:
        for call in result.tool_calls:
            if call["name"] == "route_back_to_thinking":
                target_phase = "thinking"
                break
                
    if target_phase:
        return {"messages": [result], "response": result.content, "current_phase": target_phase}
    else:
        return {"messages": [result], "response": result.content}


def _seed_welcome_slots(cursor, user_id: str):
    """Seed the 15 welcome slots from welcome.txt for a new user."""
    with open(WELCOME_TXT_PATH, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()][:NUM_WELCOME_SLOTS]
    # Pad if welcome.txt has fewer than 15 lines
    while len(lines) < NUM_WELCOME_SLOTS:
        lines.append("Welcome back. What shall we work on today?")
    for slot, msg in enumerate(lines):
        cursor.execute(
            "INSERT OR IGNORE INTO welcome_messages (user_id, slot, message, is_personalized) VALUES (?, ?, ?, 0)",
            (user_id, slot, msg),
        )
    cursor.execute(
        "INSERT OR IGNORE INTO welcome_state (user_id, current_index) VALUES (?, 0)",
        (user_id,),
    )


async def generate_welcome_tasks(user_id: str) -> str:
    """
    Serves the next message in the 15-slot cycle for this user.
    Seeds the slots from welcome.txt on first use.
    Advances the index by 1 after each session (wraps at 15).
    """
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()

    try:
        # Seed slots if this user has never had a welcome session
        cursor.execute(
            "SELECT COUNT(*) FROM welcome_messages WHERE user_id = ?", (user_id,)
        )
        count = cursor.fetchone()[0]
        if count == 0:
            _seed_welcome_slots(cursor, user_id)
            conn.commit()
            print(f"[WELCOME] Seeded 15 slots for user {user_id} from welcome.txt")

        # Get current index
        cursor.execute(
            "SELECT current_index FROM welcome_state WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        current_index = row[0] if row else 0

        # Determine if the user is "new" (less than 10 messages)
        cursor.execute(
            "SELECT COUNT(*) FROM steps JOIN threads ON steps.threadId = threads.id WHERE threads.userIdentifier = ? AND steps.type = 'user_message'",
            (user_id,),
        )
        msg_count_row = cursor.fetchone()
        msg_count = msg_count_row[0] if msg_count_row else 0
        is_established = msg_count >= 10

        message = "Welcome back. Ready when you are."

        if is_established:
            # Lazy (Just-In-Time) Generation strategy for established users
            cursor.execute(
                "SELECT fact_key, fact_value FROM atomic_facts WHERE user_id = ? ORDER BY RANDOM() LIMIT 1",
                (user_id,),
            )
            fact_row = cursor.fetchone()
            if fact_row:
                fact_key, fact_value = fact_row
                # Fetch the user's name
                cursor.execute(
                    "SELECT fact_value FROM atomic_facts WHERE user_id = ? AND fact_key = 'name'",
                    (user_id,),
                )
                name_row = cursor.fetchone()
                name = name_row[0] if name_row else ""

                try:
                    chain = welcome_message_prompt | welcome_message_llm
                    result = await chain.ainvoke(
                        {"name": name, "fact_key": fact_key, "fact_value": fact_value}
                    )
                    raw = result.content
                    if isinstance(raw, list):
                        message = "".join(
                            p.get("text", "") if isinstance(p, dict) else str(p)
                            for p in raw
                        ).strip()
                    else:
                        message = raw.strip()
                    print(
                        f"[WELCOME] (Lazy-Gen) LLM generated: '{message}' for '{fact_key}'={fact_value}"
                    )
                except Exception as e:
                    print(
                        f"[WELCOME] (Lazy-Gen) LLM failed, falling back to preset: {e}"
                    )

        # If user is new OR lazy generation failed/didn't run
        if not is_established or message == "Welcome back. Ready when you are.":
            # Fetch message at current slot
            cursor.execute(
                "SELECT message FROM welcome_messages WHERE user_id = ? AND slot = ?",
                (user_id, current_index),
            )
            msg_row = cursor.fetchone()
            if msg_row:
                message = msg_row[0]

        # Advance index (cycle)
        next_index = (current_index + 1) % NUM_WELCOME_SLOTS
        cursor.execute(
            "INSERT OR REPLACE INTO welcome_state (user_id, current_index) VALUES (?, ?)",
            (user_id, next_index),
        )
        conn.commit()
        print(f"[WELCOME] Slot {current_index} served. Next index: {next_index}")

        # Write the picked message to public/welcome_{user_id}.txt for the frontend UI animation
        user_welcome_path = _os.path.join(_PROJECT_ROOT, "public", f"welcome_{user_id}.txt")
        with open(user_welcome_path, "w", encoding="utf-8") as f:
            f.write(message)

        return message

    except Exception as e:
        print(f"[WELCOME] Error: {e}")
        return "Welcome back. Ready when you are."
    finally:
        conn.close()


async def update_welcome_slot(
    user_id: str, fact_key: str, fact_value: str, is_priority: bool = False
):
    """
    Called after a new fact is written. Replaces the oldest preset (non-personalized)
    slot with a personalized message. Priority facts (project/task etc.) are placed
    at the very NEXT slot in the current cycle instead.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    try:
        # Fetch the user's name for the greeting
        cursor.execute(
            "SELECT fact_value FROM atomic_facts WHERE user_id = ? AND fact_key = 'name'",
            (user_id,),
        )
        name_row = cursor.fetchone()
        name = name_row[0] if name_row else ""

        # Generate a personalized short message using LLM
        chain = welcome_message_prompt | welcome_message_llm
        result = await chain.ainvoke(
            {"name": name, "fact_key": fact_key, "fact_value": fact_value}
        )
        # Gemini returns content as a list of parts, Ollama returns a string
        raw = result.content
        if isinstance(raw, list):
            new_message = "".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in raw
            ).strip()
        else:
            new_message = raw.strip()
        print(
            f"[WELCOME] LLM generated: '{new_message}' for fact '{fact_key}'={fact_value}"
        )

        if is_priority:
            # Place at the next slot in the cycle (the one that will be served next session)
            cursor.execute(
                "SELECT current_index FROM welcome_state WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
            target_slot = row[0] if row else 0
            print(
                f"[WELCOME] Priority fact '{fact_key}' → slot {target_slot} (next in cycle)"
            )
        else:
            # Replace the oldest preset slot (lowest slot number that is not yet personalized)
            cursor.execute(
                "SELECT slot FROM welcome_messages WHERE user_id = ? AND is_personalized = 0 ORDER BY slot ASC LIMIT 1",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                # All slots are already personalized — overwrite the one whose fact is oldest
                cursor.execute(
                    "SELECT slot FROM welcome_messages WHERE user_id = ? ORDER BY slot ASC LIMIT 1",
                    (user_id,),
                )
                row = cursor.fetchone()
            target_slot = row[0] if row else 0

        cursor.execute(
            "UPDATE welcome_messages SET message = ?, is_personalized = 1, fact_key = ? WHERE user_id = ? AND slot = ?",
            (new_message, fact_key, user_id, target_slot),
        )
        conn.commit()
        print(
            f"[WELCOME] Slot {target_slot} replaced with personalized message: {new_message}"
        )

        # Log to a text file so the user can easily see the generated messages
        log_path = _os.path.join(_PROJECT_ROOT, "generated_welcomes.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{fact_key}]: {new_message}\n")

    except Exception as e:
        print(f"[WELCOME] Failed to update slot: {e}")
    finally:
        conn.close()


async def fast_llm_node(state: AgentState):
    print("running fast llm first")
    chain = fast_llm_prompt | fast_llm
    user_query = state.get("user_request", "")
    messages = state.get("messages", [])
    result = await chain.ainvoke({"user_query": user_query, "messages": messages})
    return {"messages": [result], "response": result.content}


async def memory_update_node(state: AgentState):
    print("Updating_memory...")

    # Get user identifier from Chainlit if available, default to "1"
    try:
        user_id = context.session.user.identifier if context.session.user else "1"
    except Exception:
        user_id = "1"

    # Fetch existing facts directly from DB
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT fact_key, fact_value, category FROM atomic_facts WHERE user_id = ?",
            (user_id,),
        )
        rows = cursor.fetchall()
        existing_memories = [
            {"fact_key": r[0], "fact_value": r[1], "category": r[2]} for r in rows
        ]
    except Exception as e:
        print(f"Error fetching memory: {e}")
        existing_memories = []

    messages = state.get("messages", [])
    if not messages:
        conn.close()
        return state

    # Determine if user is established
    cursor.execute(
        "SELECT COUNT(*) FROM steps JOIN threads ON steps.threadId = threads.id WHERE threads.userIdentifier = ? AND steps.type = 'user_message'",
        (user_id,),
    )
    msg_count_row = cursor.fetchone()
    msg_count = msg_count_row[0] if msg_count_row else 0
    is_established = msg_count >= 10

    if is_established and len(messages) % 5 != 0:
        # Throttle memory extraction for established users: only run every 5 messages in this thread
        print(
            f"[MEMORY] Skipping fact extraction (throttled). message count: {len(messages)}"
        )
        conn.close()
        return {"learned_features": existing_memories}

    # Get last 5 messages for recent context (including the new user message)
    recent_messages = messages[-5:]
    chat_context = ""
    for m in recent_messages:
        role = "User" if isinstance(m, HumanMessage) else "AI"
        chat_context += f"{role}: {m.content}\n\n"

    # Construct input
    combined_input = f"Existing memories:\n{existing_memories}\n\nRecent Conversation Context:\n{chat_context}"
    chain = memory_extract_llm_prompt | memory_update_llm

    try:
        print(f"[MEMORY] Invoking LLM for fact extraction (user_id={user_id})...")
        result = await chain.ainvoke(
            {"memories": [HumanMessage(content=combined_input)]}
        )
        facts = getattr(result, "facts", [])
        print(
            f"[MEMORY] LLM returned {len(facts)} facts: {[(f.fact_key, f.fact_value) for f in facts]}"
        )

        # Bulk UPSERT back to database
        if facts:
            sql = """
            INSERT INTO atomic_facts (id, user_id, fact_key, fact_value, category)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, fact_key) DO UPDATE SET
                fact_value=excluded.fact_value,
                category=excluded.category,
                last_updated=CURRENT_TIMESTAMP
            """
            data = [
                (str(uuid.uuid4()), user_id, f.fact_key, f.fact_value, f.category)
                for f in facts
            ]
            cursor.executemany(sql, data)
            conn.commit()
            print(
                f"[DB WRITE] Memory updated successfully: {cursor.rowcount} rows affected."
            )
            print(f"[DB WRITE] Data written: {data}")

            # 1-Fetch Optimization: Instead of re-querying, just update our local list
            for new_fact in facts:
                # Check if it exists and update it, else append
                found = False
                for existing in existing_memories:
                    if existing["fact_key"] == new_fact.fact_key:
                        existing["fact_value"] = new_fact.fact_value
                        existing["category"] = new_fact.category
                        found = True
                        break
                if not found:
                    existing_memories.append(
                        {
                            "fact_key": new_fact.fact_key,
                            "fact_value": new_fact.fact_value,
                            "category": new_fact.category,
                        }
                    )

            # Close the connection BEFORE calling update_welcome_slot
            # so it doesn't hold a write lock that blocks the inner connection
            conn.close()
            conn = None

            # Update the welcome slot cycle for each new fact
            if not is_established:
                for new_fact in facts:
                    is_priority = any(
                        k in new_fact.fact_key for k in PRIORITY_FACT_KEYS
                    )
                    print(
                        f"[MEMORY] Calling update_welcome_slot for fact '{new_fact.fact_key}' (priority={is_priority})..."
                    )
                    try:
                        await update_welcome_slot(
                            user_id, new_fact.fact_key, new_fact.fact_value, is_priority
                        )
                        print(
                            f"[MEMORY] update_welcome_slot completed for '{new_fact.fact_key}'"
                        )
                    except Exception as slot_err:
                        import traceback

                        print(
                            f"[MEMORY] update_welcome_slot FAILED for '{new_fact.fact_key}': {slot_err}"
                        )
                        traceback.print_exc()
            else:
                print(
                    f"[MEMORY] Skipping update_welcome_slot for {len(facts)} facts because user is established (lazy generation is active)."
                )
        else:
            print("[MEMORY] No new facts extracted by LLM — nothing to update.")

    except Exception as e:
        import traceback

        print(f"[MEMORY] FAILED during memory extraction/write: {e}")
        traceback.print_exc()

    if conn:
        conn.close()
    return {"learned_features": existing_memories}


async def orchestrator_llm_node(state: AgentState):
    print("\n" + "="*50)
    print("🤖 [DEBUG] --- ENTERED ORCHESTRATOR NODE ---")
    print("="*50 + "\n")
    is_project = state.get("is_project", False)
    user_profile = state.get("learned_features", [])
    welcome_context = state.get("welcome_context", "")

    # State updates to return
    state_updates = {}

    # Build injected context messages
    context_parts = []
    
    if is_project:
        project_path = state.get("projet_path")
        
        # --- .model/ Entry Workflow ---
        if project_path and _os.path.exists(project_path):
            # Generate directory tree if not already done
            if not state.get("project_structure"):
                state_updates["project_structure"] = _get_directory_tree(project_path)
                state["project_structure"] = state_updates["project_structure"]
            
            # Ensure .model/ directory exists
            model_dir = _os.path.join(project_path, ".model")
            if not _os.path.exists(model_dir):
                _os.makedirs(model_dir, exist_ok=True)
                print("[ORCHESTRATOR] Created .model/ directory")
            
            # Read project_memory.md
            if not state.get("project_memory"):
                mem_path = _os.path.join(model_dir, "project_memory.md")
                if _os.path.exists(mem_path):
                    with open(mem_path, "r", encoding="utf-8") as f:
                        pm_content = f.read()
                    if pm_content.strip():
                        state_updates["project_memory"] = pm_content
                        state["project_memory"] = pm_content
                        print(f"[ORCHESTRATOR] Loaded project_memory.md ({len(pm_content)} chars)")
            
            # Read tasks.md
            if not state.get("pending_tasks"):
                tasks_path = _os.path.join(model_dir, "tasks.md")
                if _os.path.exists(tasks_path):
                    with open(tasks_path, "r", encoding="utf-8") as f:
                        tasks_content = f.read()
                    if tasks_content.strip():
                        state_updates["pending_tasks"] = tasks_content
                        state["pending_tasks"] = tasks_content
                        print(f"[ORCHESTRATOR] Loaded tasks.md ({len(tasks_content)} chars)")
            
            # Read project_timeline.md
            if not state.get("project_timeline"):
                tl_path = _os.path.join(model_dir, "project_timeline.md")
                if _os.path.exists(tl_path):
                    with open(tl_path, "r", encoding="utf-8") as f:
                        tl_content = f.read()
                    if tl_content.strip():
                        state_updates["project_timeline"] = tl_content
                        state["project_timeline"] = tl_content
                        print(f"[ORCHESTRATOR] Loaded project_timeline.md ({len(tl_content)} chars)")
            
            # Read learned_lessons.md
            if not state.get("project_learned_features"):
                ll_path = _os.path.join(model_dir, "learned_lessons.md")
                if _os.path.exists(ll_path):
                    with open(ll_path, "r", encoding="utf-8") as f:
                        ll_content = f.read()
                    if ll_content.strip():
                        state_updates["project_learned_features"] = [ll_content]
                        state["project_learned_features"] = [ll_content]
                        print(f"[ORCHESTRATOR] Loaded learned_lessons.md ({len(ll_content)} chars)")

        # --- Build context injection ---
        if state.get("project_structure"):
            context_parts.append(f"[PROJECT DIRECTORY STRUCTURE]:\n{state['project_structure']}\n(Use this to understand the current files without needing to run ls)")
        if state.get("project_memory"):
            context_parts.append(f"[PROJECT MEMORY]:\n{state['project_memory']}")
        if state.get("pending_tasks"):
            context_parts.append(f"[PENDING TASKS - NOTIFY USER]:\n{state['pending_tasks']}\nIMPORTANT: There are pending tasks from a previous session. Immediately notify the user about these before doing anything else.")
        if state.get("project_timeline"):
            context_parts.append(f"[PROJECT TIMELINE]:\n{state['project_timeline']}")
        if state.get("project_learned_features"):
            context_parts.append(f"[LEARNED LESSONS]:\n{state['project_learned_features']}")

    if user_profile:
        context_parts.append(f"[USER PROFILE MEMORIES]:\n{user_profile}")
    profile_msg = (
        [HumanMessage(content="[SYSTEM CONTEXT]\n" + "\n\n".join(context_parts))]
        if context_parts
        else []
    )
    
    welcome_msg_list = []
    if welcome_context:
        welcome_msg_list = [AIMessage(content=welcome_context)]

    # Read terminal_access from Chainlit user session, default to True if not explicitly False
    terminal_access = True
    try:
        settings = cl.user_session.get("settings", {})
        terminal_access = settings.get("terminal_access", True)
    except Exception:
        pass

    if terminal_access:
        print("Terminal access is enabled! Running orchestrator agent (access to terminal)")
        chain = orchestrator_project_llm_prompt | orchestrator_project_llm
        user_query = state.get("user_request", "")
        messages = state.get("messages", [])

        # Inject the profile message right before the chat history
        invocation_messages = profile_msg + welcome_msg_list + messages
        result = await chain.ainvoke(
            {"user_query": user_query, "messages": invocation_messages}
        )
        print(result)
    else:
        print("Terminal access disabled. Running chat mode.")
        chain = orchestrator_llm_prompt | orchestrator_llm
        user_query = state.get("user_request", "")
        messages = state.get("messages", [])

        # Inject the profile message right before the chat history
        invocation_messages = profile_msg + welcome_msg_list + messages
        result = await chain.ainvoke(
            {"user_query": user_query, "messages": invocation_messages}
        )
        print(result)
        
    target_phase = None
    if hasattr(result, "tool_calls") and result.tool_calls:
        for call in result.tool_calls:
            if call["name"] == "route_to_thinking":
                target_phase = "thinking"
                break
                
    if target_phase:
        return {**state_updates, "messages": [result], "response": result.content, "current_phase": target_phase}
    else:
        return {**state_updates, "messages": [result], "response": result.content}
