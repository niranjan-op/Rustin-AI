import chainlit as cl
import ollama_manager as m
from database import init_sqlite_db
import os
import base64

import chainlit as cl
from chainlit.data import BaseDataLayer
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.base import BaseStorageClient
from chainlit.input_widget import Select
from chainlit.types import ThreadDict
from langchain_core.messages import AIMessage, HumanMessage

import models as md

# Import the compiled graph
from agent import app_graph


# define ollama_port for  further connections
ollama_port = m.is_ollama_running()

## Fetch all ollama models code
    ## TODO
    
init_sqlite_db("test.db")
connection_string = "sqlite+aiosqlite:///./test.db"
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


# @cl.on_chat_start
# async def on_start_chat():
#     settings = await cl.ChatSettings(
#         [
#             Select(
#                 id="Available models",
#                 label="Models",
#                 values=all_models.keys(),
#                 initial_index=0,
#             )
#         ]
#     ).send()
#     cl.user_session.set("settings", settings)

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
                        "description" : el.get("description")
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

        # Stream the execution of the graph using astream_events
        async for event in app_graph.astream_events(state, version="v2"):
            kind = event.get("event")
            
            # Stream LLM tokens in real-time
            if kind == "on_chat_model_stream":
                content = event.get("data", {}).get("chunk", {}).content
                if content:
                    await msg.stream_token(content)
                    assistant_msg += content
            
            # Capture the final state at the end of the top-level workflow sequence
            elif kind == "on_chain_end":
                output = event.get("data", {}).get("output")
                if isinstance(output, dict) and "messages" in output:
                    final_state = output

        # If a final state was returned, retrieve the full messages list and assistant response
        if final_state:
            final_messages = final_state.get("messages", [])
            # Find the last message that is an AIMessage to determine assistant response
            extracted_msg = None
            for m in reversed(final_messages):
                if isinstance(m, AIMessage) or getattr(m, "type", None) == "ai":
                    extracted_msg = m.content
                    break
            if extracted_msg:
                assistant_msg = extracted_msg
            else:
                assistant_msg = "Agent processed the request but returned no response."
            cl.user_session.set("chat_history", final_messages)
        else:
            # Fallback if final state wasn't captured: append manual messages
            if not assistant_msg:
                assistant_msg = "Agent processed the request but returned no specific response."
            current_history = cl.user_session.get("chat_history", [])
            new_history = current_history + [
                HumanMessage(content=message.content),
                AIMessage(content=assistant_msg)
            ]
            cl.user_session.set("chat_history", new_history)

    except Exception as e:
        assistant_msg = f"Agent Error: {str(e)}"

    msg.content = assistant_msg
    await msg.update()
