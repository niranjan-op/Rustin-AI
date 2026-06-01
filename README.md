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
   git clone https://github.com/your-username/autonomous-agent.git
   cd autonomous-agent
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
   pip install chainlit langchain langchain-ollama langgraph ollama aiosqlite sqlalchemy pydantic
   ```

4. **Start Ollama:**
   Ensure Ollama is running in the background and that you have pulled your preferred models (e.g., Llama 3, Mistral, or CodeQwen).
   ```bash
   ollama run llama3
   ```

### Usage

To start the agent's web interface, run the Chainlit server from the root directory:

```bash
chainlit run app.py -w
```

This will automatically start the backend Node server and open the web interface in your default browser (usually at `http://localhost:8000`). 

From the interface, you can start a new chat, ask the agent to write code, upload images for vision tasks, and give the agent access to run safe terminal commands by toggling the "Terminal Access" setting!

## 🛡️ Security

The backend sandbox server (`public/server/app.js`) implements command filtering and path jailing to prevent the agent from accidentally running destructive system commands or traversing directories outside the active project workspace. 


