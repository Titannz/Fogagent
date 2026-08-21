# FogAgent

**FogAgent** is a personal, local-first AI Agent designed to run entirely on local hardware with GPU acceleration, persistent contextual memory, structured knowledge management, and a human-controlled Study Mode.

---

## Key Features

- **Local-First & Offline:** Runs locally through [Ollama](https://ollama.com/) with native GPU acceleration (AMD Radeon 780M / Vulkan / CUDA / ROCm).
- **Controlled Study Mode (Human-in-the-Loop Learning):**
  - Learning only happens when explicitly authorized (`youcanstudy`).
  - Study Mode can be stopped at any time (`byebye`) without deleting previously learned knowledge.
  - Incoming knowledge passes an evaluation and structured extraction stage before storage (never blindly saving arbitrary text).
- **Separated Memory & Knowledge Systems:**
  - **Memory System (`memory.db`):** Stores user-specific context, preferences, tasks, and recent conversation history.
  - **Knowledge System (`knowledge.db`):** Stores evaluated, structured general concepts, definitions, and technical knowledge in SQLite.
- **Dynamic Context Injection:** Retrieves relevant memories and knowledge entries to augment the LLM prompt without blowing up the context window.
- **Real-Time Streaming CLI:** Fast token streaming output directly to the terminal with UTF-8 support on Windows.

---

## Project Structure

```text
Fogagent/
├── agent/
│   ├── __init__.py
│   ├── agent.py              # Main Agent combining Memory, Knowledge, and Study Mode
│   └── study_engine.py       # Knowledge extraction & evaluation engine
├── config/
│   ├── __init__.py
│   └── settings.py           # Centralized configuration (model, context, paths)
├── knowledge/
│   ├── __init__.py
│   └── knowledge_manager.py  # SQLite storage for structured knowledge
├── memory/
│   ├── __init__.py
│   └── memory_manager.py     # SQLite storage for user facts and conversation context
├── models/
│   ├── __init__.py
│   └── ollama_model.py       # Ollama client with token streaming and options
├── data/                     # Local SQLite databases (gitignored)
│   ├── memory/
│   └── knowledge/
├── tests/
│   ├── test_config.py
│   ├── test_agent.py
│   ├── test_memory.py
│   ├── test_knowledge.py
│   └── test_study_mode.py
├── main.py                   # Interactive terminal interface
├── requirements.txt
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running with `qwen3:8b` (or your preferred local model).
  ```bash
  ollama pull qwen3:8b
  ```

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Titannz/Fogagent.git
cd Fogagent

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

Start FogAgent:
```bash
python main.py
```

### CLI Commands

| Command | Action |
| :--- | :--- |
| `youcanstudy` | Enable Study Mode (allow FogAgent to extract and learn new knowledge). |
| `byebye` | Disable Study Mode (stop learning; retains all previously learned knowledge). |
| `remember <key>: <value>` | Explicitly store a user preference or fact into Memory. |
| `memories` | List all stored persistent memories. |
| `knowledge` | List all learned structured knowledge entries. |
| `status` | Display current model, context window, and database record counts. |
| `exit` / `quit` | Exit the CLI. |

---

## Running Tests

Run the automated unit test suite:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## Roadmap

- [x] **Phase 1:** Ollama + Qwen3:8b GPU Acceleration (AMD Radeon 780M / Vulkan).
- [x] **Phase 2:** Modular Agent Architecture & Streaming.
- [x] **Phase 3:** Persistent Local MemoryManager.
- [x] **Phase 4:** Structured SQLite KnowledgeManager.
- [x] **Phase 5:** Controlled Study Mode Learning Engine.
- [ ] **Phase 6:** Semantic & Vector Knowledge Retrieval.
- [ ] **Phase 7:** Autonomous Web Research Engine.
- [ ] **Phase 8:** Extensible Tool System.
