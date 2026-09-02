# FogAgent

**FogAgent** is a personal, local-first, offline AI Agent designed to run entirely on local hardware with GPU acceleration, persistent contextual memory, structured knowledge management, a human-controlled Study Mode, and strict data quality gates.

---

## Key Features

- **100% Local-First & Safe:** Runs locally through [Ollama](https://ollama.com/) with native GPU acceleration (AMD Radeon 780M / Vulkan). No external internet dependencies, zero risk of remote prompt injections or data leaks.
- **Human-in-the-Loop & Approval Gate:**
  - Agent **never** silently writes to the knowledge database.
  - Extracted knowledge is presented in a clean verification card and only committed upon explicit human confirmation (`y/n`).
- **Loop Control & Workload Pre-Estimation:**
  - Automatically estimates processing time and token count for large documents.
  - Prompts you beforehand: *"Estimated ~3 mins on GPU. Start now? (y/n)"*.
  - If you decline, you can **defer the task to the Study Queue** to run later when the machine is cool/idle, or discard it completely.
- **Data Quality & Noise Filter:**
  - Filters out casual greetings, conversational chatter, and trivial noise before LLM extraction.
  - Enforces a strict confidence threshold ($\ge 0.85$).
  - Detects duplicate topics and potential conflicts with stored facts.
- **Separated Memory & Knowledge Systems:**
  - **Memory System (`memory.db`):** Stores user profile, preferences, hardware constraints, and recent conversation history.
  - **Knowledge System (`knowledge.db`):** Stores evaluated, structured general concepts, definitions, and technical knowledge in SQLite.
- **Deferred Study Queue (`study_queue.db`):**
  - Manages heavy reading/study workloads without blocking your live conversation.

---

## Project Structure

```text
Fogagent/
├── agent/
│   ├── __init__.py
│   ├── agent.py              # Main Agent coordinating Memory, Knowledge, and Study Mode
│   └── study_engine.py       # Knowledge extraction, quality gating & workload estimation
├── config/
│   ├── __init__.py
│   └── settings.py           # Centralized configuration (model, context, paths)
├── knowledge/
│   ├── __init__.py
│   ├── data_cleaner.py       # Noise filter, confidence validation, duplicate detection
│   ├── study_queue.py        # Deferred study queue manager in SQLite
│   └── knowledge_manager.py  # SQLite storage for structured knowledge with auditing
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
│   ├── test_study_mode.py
│   ├── test_data_cleaner.py
│   └── test_study_queue.py
├── main.py                   # Interactive terminal interface
├── requirements.txt
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14 on Windows 11)
- [Ollama](https://ollama.com/) with `qwen3:8b` (configured with `OLLAMA_IGPU_ENABLE=1` for AMD Radeon 780M Vulkan acceleration).

### 2. Quickstart
```bash
git clone https://github.com/Titannz/Fogagent.git
cd Fogagent

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run FogAgent
python main.py
```

---

## CLI Commands

| Command | Category | Action |
| :--- | :--- | :--- |
| `youcanstudy` | Study Mode | Enable Study Mode (allow FogAgent to extract and learn new knowledge). |
| `byebye` | Study Mode | Disable Study Mode (stop learning; retains all previously learned knowledge). |
| `queue` | Queue | List all pending study items with estimated processing times. |
| `study_now <id>` | Queue | Process a specific deferred study item from the queue. |
| `queue_drop <id>` | Queue | Remove an item from the study queue. |
| `audit` | Quality | Audit the knowledge base for low-confidence entries and duplicate topics. |
| `delete <id>` | Quality | Permanently delete a specific knowledge entry by ID. |
| `profile` | Memory | View personalized profile, preferences, and hardware constraints. |
| `remember <k>: <v>` | Memory | Explicitly store a user preference or fact into Memory. |
| `memories` | Memory | List all stored persistent memories. |
| `knowledge` | Knowledge | List all learned structured knowledge entries. |
| `status` | System | Display current model, context window, and database record counts. |
| `exit` / `quit` | System | Exit the CLI. |

---

## Running Tests

Run the complete 25 automated unit tests:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## Roadmap

- [x] **Phase 1:** Ollama + Qwen3:8b GPU Acceleration (AMD Radeon 780M / Vulkan).
- [x] **Phase 2:** Modular Agent Architecture & Streaming CLI.
- [x] **Phase 3:** Persistent Local MemoryManager (`memory.db`).
- [x] **Phase 4:** Structured SQLite KnowledgeManager (`knowledge.db`).
- [x] **Phase 5:** Controlled Study Mode Learning Engine (`youcanstudy` / `byebye`).
- [x] **Phase 6:** Data Quality Pipeline, Loop Control, Workload Estimator & Deferred Study Queue.
- [x] ~~**Phase 7:** Autonomous Web Researcher (Removed for security and offline integrity)~~.
- [ ] **Phase 8:** Secure Local Tools (Document parsing with approval, deterministic execution).
- [ ] **Phase 9:** Autonomous Planning & Task Decomposition DAG.
