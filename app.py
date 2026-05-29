import base64
import os

import chainlit as cl
from chainlit.data import BaseDataLayer
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.base import BaseStorageClient
from chainlit.input_widget import Select
from chainlit.types import ThreadDict
from langchain_core.messages import AIMessage, HumanMessage

import models as md
import ollama_manager as m

# Import the compiled graph
from agent import app_graph
from database import init_sqlite_db

# define ollama_port for  further connections
ollama_port = m.is_ollama_running()

## Fetch all ollama models code
## TODO

init_sqlite_db(".files/test.db")
connection_string = "sqlite+aiosqlite:///./.files/test.db"
STORAGE_DIR = os.path.join(os.getcwd(), "public")
os.makedirs(STORAGE_DIR, exist_ok=True)


class LocalBlobClient(BaseStorageClient):
    async def init(self):
        pass

    async def upload_file(
        self,
        object_key: str,
        data: bytes | str = b"",
        mime: str = "application/octet-stream",
        overwrite: bool = True,
        **kwargs,
    ):
        if not data:
            raise ValueError("No file data provided to upload_file")

        file_path = os.path.join(STORAGE_DIR, object_key)

        # Ensure that any nested directories in object_key exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write the binary data to your local disk
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(file_path, mode) as f:
            f.write(data)
        # Return the /public/ URL that Chainlit serves natively
        clean_key = object_key.replace("\\", "/")
        servable_url = f"/public/{clean_key}"
        return {"object_key": object_key, "url": servable_url}

    async def get_read_url(self, object_key: str):
        # Return the /public/ URL for the frontend
        clean_key = object_key.replace("\\", "/")
        return f"/public/{clean_key}"

    async def delete_file(self, object_key: str):
        file_path = os.path.join(STORAGE_DIR, object_key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    async def close(self):
        pass


@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(
        conninfo=connection_string, storage_provider=LocalBlobClient()
    )


@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    user = cl.User(identifier=username)
    await get_data_layer().create_user(user)
    return user


@cl.on_chat_start
async def on_start_chat():
    settings = await cl.ChatSettings(
        [
            Select(
                id="chat-type",
                label="Chat Type",
                values=["normal", "project"],
                initial_index=0,
            )
        ]
    ).send()
    cl.user_session.set("settings", settings)


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    history = []
    for step in thread["steps"]:
        # Extract element info if present in the step
        elements_info = []
        if "elements" in step and step["elements"]:
            for el in step["elements"]:
                elements_info.append(
                    {
                        "name": el.get("name"),
                        "url": el.get("url"),
                        "type": el.get("type"),
                        "description": el.get("description"),
                    }
                )

        content = step["output"]
        if elements_info:
            content += f"\n\n[Attached Elements: {elements_info}]"

        if step["type"] == "user_message":
            history.append(HumanMessage(content=content))
        elif step["type"] == "assistant_message":
            history.append(AIMessage(content=content))

    cl.user_session.set("chat_history", history)

    # settings = await cl.ChatSettings(
    #     [
    #         Select(
    #             id="Agent",
    #             label='Agent',
    #             values=['Fast', 'Planning', 'Intuitive Planning'],
    #             initial_index=0
    #         )
    #     ]
    # ).send()
    # cl.user_session.set("settings", settings)


@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("settings", settings)
    print("Settings updated:", settings)


def encode_image(image_path):
    """Returns the base64 string for an image file."""
    with open(image_path, "rb") as image_file:
        print(
            "Converting image to base64: ",
        )
        string = base64.b64encode(image_file.read()).decode("utf-8")
        return string


@cl.on_message
async def on_message(message: cl.Message):
    settings = cl.user_session.get("settings", {})
    agent_type = settings.get("Agent", "Fast")
    current_settings = cl.user_session.get("settings")
    # selected_model = current_settings.get("Available models")
    # md.select_model(selected_model)

    # Extract element info and encode images to base64
    elements_data = []
    if message.elements:
        for el in message.elements:
            element_info = {
                "name": el.name,
                "path": getattr(el, "path", None),
                "url": getattr(el, "url", None),
                "mime": getattr(el, "mime", None),
            }
            print("Before", "-" * 64, element_info)
            # If it's an image, add the base64 data for the VLM
            if el.mime and "image" in el.mime and el.path:
                try:
                    element_info["base64"] = encode_image(el.path)
                    print("Successfully added base64")
                except Exception as e:
                    print(f"Error encoding image: {e}")

            # print("After", "-" * 64, element_info["base64"])
            elements_data.append(element_info)

    # Get history and add current message
    history = cl.user_session.get("chat_history", [])

    state = {
        "messages": history + [HumanMessage(content=message.content)],
        "user_request": message.content,
        "agent_type": agent_type,
        "elements": elements_data,  # Pass to agent
    }

    # UI Placeholder
    msg = cl.Message(content="")
    await msg.send()

    try:
        assistant_msg = ""
        final_state = None

        def _extract_text(content):
            """Convert Gemini list-of-parts content to a plain string."""
            if not content:
                return ""
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                return "".join(text_parts)
            return str(content)

        # Stream the execution of the graph using astream_events
        async for event in app_graph.astream_events(state, version="v2"):
            kind = event.get("event")

            # Stream LLM tokens in real-time
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk is None:
                    continue
                # Safely access .content — chunk could be an AIMessageChunk or other type
                raw_content = getattr(chunk, "content", None)
                text = _extract_text(raw_content)
                if text:
                    await msg.stream_token(text)
                    assistant_msg += text

            # Capture the final state at the end of the top-level workflow sequence
            elif kind == "on_chain_end":
                output = event.get("data", {}).get("output")
                if isinstance(output, dict) and "messages" in output:
                    final_state = output

        print(f"[DEBUG] Streamed assistant_msg length: {len(assistant_msg)}")

        # --- Response extraction with fallback chain ---
        if final_state:
            final_messages = final_state.get("messages", [])
            print(f"[DEBUG] Final state has {len(final_messages)} messages")

            # Strategy 1: Use streamed text if we accumulated any
            if assistant_msg.strip():
                print("[DEBUG] Using Strategy 1: streamed text")
            else:
                # Strategy 2: Find the last AIMessage with non-empty text content
                extracted_msg = None
                for m_item in reversed(final_messages):
                    if (
                        isinstance(m_item, AIMessage)
                        or getattr(m_item, "type", None) == "ai"
                    ):
                        text = _extract_text(m_item.content)
                        if text.strip():
                            extracted_msg = text
                            break

                if extracted_msg:
                    assistant_msg = extracted_msg
                    print(
                        f"[DEBUG] Using Strategy 2: AIMessage content (len={len(extracted_msg)})"
                    )
                else:
                    # Strategy 3: Build a response from tool calls and their results
                    from langchain_core.messages import ToolMessage

                    tool_summaries = []
                    for i, m_item in enumerate(final_messages):
                        if isinstance(m_item, ToolMessage):
                            tool_name = getattr(m_item, "name", None) or "tool"
                            tool_output = m_item.content or "(no output)"
                            tool_summaries.append(
                                f"**{tool_name}** result:\n```\n{tool_output}\n```"
                            )

                    if tool_summaries:
                        assistant_msg = (
                            "Here are the results from the sandbox:\n\n"
                            + "\n\n".join(tool_summaries)
                        )
                        print(
                            f"[DEBUG] Using Strategy 3: tool results ({len(tool_summaries)} tools)"
                        )
                    else:
                        assistant_msg = (
                            "Agent processed the request but returned no response."
                        )
                        print("[DEBUG] All strategies failed — using fallback message")

            cl.user_session.set("chat_history", final_messages)
        else:
            print("[DEBUG] No final_state captured from on_chain_end events")
            if not assistant_msg:
                assistant_msg = (
                    "Agent processed the request but returned no specific response."
                )
            current_history = cl.user_session.get("chat_history", [])
            new_history = current_history + [
                HumanMessage(content=message.content),
                AIMessage(content=assistant_msg),
            ]
            cl.user_session.set("chat_history", new_history)

    except Exception as e:
        import traceback

        traceback.print_exc()
        assistant_msg = f"Agent Error: {str(e)}"

    # Ensure we always have a string
    if not isinstance(assistant_msg, str):
        assistant_msg = _extract_text(assistant_msg)
    if not assistant_msg.strip():
        assistant_msg = "Agent completed but produced no visible output."

    print(f"[DEBUG] Final msg.content = {repr(assistant_msg[:200])}")
    msg.content = assistant_msg
    await msg.update()
