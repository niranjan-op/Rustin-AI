# Rustin AI. 🤖
Assistant by Design. Developer by Nature.

Welcome to the **Rustin AI** repository! This is a powerful, locally-hosted AI agent built on top of [Chainlit](https://chainlit.io), [LangGraph](https://langchain-ai.github.io/langgraph/), and [Ollama](https://ollama.com/). It is designed to act as your personal chatting assistant and coding agent capable of writing code, managing files, and executing terminal commands autonomously.

## ✨ Features

- **Conversational UI**: Clean, interactive, and responsive web interface powered by Chainlit.
- **Local AI Execution**: Native integration with Ollama for running open-source LLMs locally, ensuring complete privacy and fast inference.
- **Graph-Based Reasoning**: Implements LangGraph for complex reasoning loops, tool-use coordination, and state management.
- **Sandboxed Execution Environment**: Features an integrated local Node.js backend server (`public/server/app.js`) to safely execute terminal commands on behalf of the agent, complete with security validations and path jailing.
- **Vision Support**: Fully capable of processing image uploads and converting them for Vision-Language Models (VLMs).
- **Project Isolation**: Maintains separate workspace states and local SQLite chat histories across different threads and development projects.
- **Native Git Management**: Capable of reading `.gitignore` files, managing git repositories, and generating structured artifacts.

## 📸 Screenshots


![Welcome Screen](/src/Chat_Interface.png)
*Agent Welcome Screen and Project Setup*
![Working Agent ](/src/Agent.png)

## 🚀 Getting Started

### Prerequisites

To run this project, you will need the following installed on your system:
- **Python 3.10+**
- **Node.js** (Required for the terminal sandbox backend)
- **Git**
- **[Ollama](https://ollama.com/)** (Required for local LLM execution)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/niranjan-op/Rustin-AI
   cd Rustin-AI
   ```

2. **Create a virtual environment:**
   ```bash
   # On Windows
   python -m venv .venv
   .venv\Scripts\activate

   # On Mac/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the Python dependencies:**
   Ensure your virtual environment is active, then install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a .env file**:
   Create a .env file in the same directory, run the following command and paste it into the .env
   ```bash
   chainlit create-secret
   ```
  Add your google genai api key into the env file as 
  ```bash
  GOOGLE_API_KEY = ""
  ```

  **NOTE:**
  The project supports use of ollama models. To use them, modify the base_llm models.py file as:
  ```python
  base_llm = ChatOllama(
    model="model_name", temperature=0.5, base_url="http://127.0.0.1:11434"
    )
  ```
  
### Usage

To start the agent's GUI interface, run the Chainlit server from the root directory:

```bash
py main.py
```

This will automatically start the backend Node server and open a GUI interface to the Rustin AI Agent.

From the interface, you can start a new chat, ask the agent to write code, upload images for vision tasks, and give the agent access to run safe terminal commands by toggling the "Terminal Access" setting!

## 🛡️ Security

The backend sandbox server (`public/server/app.js`) implements command filtering and path jailing to prevent the agent from accidentally running destructive system commands or traversing directories outside the active project workspace.
