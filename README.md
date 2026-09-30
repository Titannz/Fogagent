# FogAgent

**FogAgent** is a personal, local-first, offline AI Agent designed to run entirely on local hardware with GPU acceleration, persistent contextual memory, structured knowledge management, human-controlled Study Mode, and strict data quality gates.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([User Terminal Input]) --> Router{Input Router}

    %% Commands Branch
    Router -->|CLI Command e.g. status, queue, byebye| CMDHandler[Command Handler]
    CMDHandler --> TerminalDisplay[Terminal Output]

    %% Context Assembly
    Router -->|Query / Prompt| ContextEngine[Context Assembly Engine]
    
    subgraph Storage [Local SQLite Storage]
        MemDB[(memory.db\nUser Profile & Chat History)]
        KnowDB[(knowledge.db\n35+ Structured Theorems)]
        QueueDB[(study_queue.db\nDeferred Study Queue)]
    end

    ContextEngine <-->|Filter Stop-words & Fetch Recent History| MemDB
    ContextEngine <-->|Selective Keyword Match| KnowDB
    SysPrompt[System Prompt\nLanguage Purity & Unicode Math Rules] --> ContextEngine

    %% LLM Inference
    ContextEngine -->|Augmented Context Prompt| Ollama[Ollama Server :11434]
    
    subgraph Compute [Local Hardware Acceleration]
        Ollama <-->|100% GPU Offload via Vulkan| GPU[AMD Radeon 780M GPU\nQwen3:8b @ 8192 Context]
    end

    %% Output Pipeline
    Ollama -->|Token Stream| MathFormatter[Math Formatter\nConverts LaTeX to Unicode: ≤, ≥, ∈, →]
    MathFormatter --> TerminalDisplay
    TerminalDisplay --> User

    %% Guarded Study Pipeline
    Router -.->|If Study Mode: ON & Factual Input| StudyGuard{Data Cleaner & Noise Guard}
    StudyGuard -.->|Skip Questions e.g. 'cho tôi ví dụ'| SkipStudy[Bypass Study - Zero Latency]
    StudyGuard -.->|Valid Factual Knowledge| ApprovalGate{Human Approval Gate\nConfirm Save? y/n}
    ApprovalGate -.->|User Approves: 'y'| KnowDB
    ApprovalGate -.->|User Declines: 'n'| Discard[Discard Candidate]

    %% Styling
    style GPU fill:#ea580c,stroke:#c2410c,stroke-width:2px,color:#fff
    style ApprovalGate fill:#dc2626,stroke:#991b1b,stroke-width:2px,color:#fff
    style Storage fill:#1e293b,stroke:#475569,stroke-width:1px,color:#fff
    style Compute fill:#1e293b,stroke:#475569,stroke-width:1px,color:#fff
```

---

## 🧠 Underlying Transformer Architecture

FogAgent uses **Qwen3:8b**, an autoregressive **Decoder-Only Transformer** evolved from the seminal *"Attention Is All You Need"* (Vaswani et al., 2017) architecture:

```mermaid
flowchart TD
    subgraph OriginalTransformer ["Classic 2017 Transformer (Encoder-Decoder)"]
        direction LR
        subgraph EncoderBlock ["Encoder (Left)"]
            EIn[Inputs] --> EEmb[Embedding + Pos] --> EMHA[Self-Attention] --> EFF[Feed-Forward]
        end
        subgraph DecoderBlock ["Decoder (Right)"]
            DIn[Outputs] --> DEmb[Embedding + Pos] --> DMasked[Masked Self-Attn] --> ECross[Cross-Attention] --> DFF[Feed-Forward] --> DOut[Softmax Probabilities]
        end
        EFF -.->|Keys & Values| ECross
    end

    subgraph ModernDecoderOnly ["Qwen3:8b Architecture in FogAgent (Decoder-Only)"]
        QIn[Tokenized Prompt] --> QEmb[Input Embedding + RoPE]
        
        subgraph TransformerBlock ["x36 Transformer Layers (100% GPU Offload)"]
            QNorm1[RMSNorm] --> QGQA[Grouped-Query Attention\nGQA with Rotary Embeddings]
            QGQA --> QAdd1((+))
            QAdd1 --> QNorm2[RMSNorm]
            QNorm2 --> QSwiGLU[SwiGLU Feed-Forward Network]
            QSwiGLU --> QAdd2((+))
        end
        
        QEmb --> TransformerBlock
        TransformerBlock --> FinalNorm[Final RMSNorm] --> Head[Linear LM Head] --> NextToken[Generated Token Stream]
    end

    style GPU fill:#ea580c,stroke:#c2410c,stroke-width:2px,color:#fff
    style ModernDecoderOnly fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    style OriginalTransformer fill:#1e293b,stroke:#64748b,stroke-width:1px,color:#fff
```

---

## Key Features

- **100% Local-First & Safe:** Powered locally by Ollama with hardware offload on AMD Radeon 780M (Vulkan). Zero internet dependencies, completely private.
- **Human-in-the-Loop & Approval Gate:**
  - Agent **never** silently modifies the knowledge base.
  - Extracted knowledge presents an interactive verification card requiring explicit confirmation (`y/n`).
- **Loop Control & Workload Pre-Estimation:**
  - Automatically estimates processing time on the GPU before analyzing heavy documents.
  - Users can proceed, defer to the **Study Queue** to learn later when the machine is cool, or cancel.
- **Low-Latency Architecture:**
  - **Smart Stop-words Filter:** Ignores conversational fillers (`cho tôi`, `ví dụ`, `tại sao`) during database retrieval to prevent unnecessary SQL latency.
  - **Bypass Double Inference:** Recognizes questions and requests during Study Mode, skipping redundant knowledge extraction calls to keep responses instant.
- **Clean Terminal Math (Unicode):**
  - Converts raw LaTeX markup (`\leq`, `\geq`, `\in`, `\forall`, `\to`, `\infty`, `\times`) into clean Unicode characters (`≤`, `≥`, `∈`, `∀`, `→`, `∞`, `×`) in real-time.
- **Structured Knowledge Store (`knowledge.db`):**
  - Pre-loaded with 47+ verified concepts (University Mathematics, Data Structures & Algorithms in Python, and Relational SQL Databases).
- **Anti-Hallucination Guard & Fact Grounding:**
  - Strict system prompts and context constraints preventing the agent from fabricating facts, APIs, formulas, or libraries when uncertain.
  - Focused low temperature (`0.3`) for deterministic, grounded reasoning.
  - Prioritizes verified local entries stored in `knowledge.db` and user profiles in `memory.db`.
- **Secure Local Tools & Human Verification Gate (Phase 8):**
  - 100% offline deterministic tools: `math_evaluator` (AST-based math parser without `eval`), `file_inspector` (sandboxed workspace viewer protecting against path traversal), `db_inspector` (read-only SQLite schemas & safe SELECT queries), and `python_runner` (isolated subprocess with execution timeouts).
  - Explicit Human Verification Gate (`y/n`) before executing actions, giving users complete control over local execution.

---

## Project Structure

```text
Fogagent/
├── agent/
│   ├── __init__.py
│   ├── agent.py              # Central Agent coordinating Memory, Knowledge, and Streaming
│   └── study_engine.py       # Knowledge extraction, quality gating & workload estimation
├── config/
│   ├── __init__.py
│   └── settings.py           # Central configuration (model, context, paths, prompts)
├── knowledge/
│   ├── __init__.py
│   ├── data_cleaner.py       # Noise filter, confidence validation, question bypass
│   ├── math_formatter.py     # Real-time LaTeX-to-Unicode math symbol formatter
│   ├── study_queue.py        # Deferred study queue in SQLite
│   └── knowledge_manager.py  # SQLite storage with stop-words search & data auditing
├── memory/
│   ├── __init__.py
│   └── memory_manager.py     # SQLite storage for user facts and conversation context
├── models/
│   ├── __init__.py
│   └── ollama_model.py       # Ollama client with token streaming
├── tools/
│   ├── __init__.py
│   ├── base_tool.py          # Abstract base tool, RiskLevel, and ToolResult
│   ├── verification_gate.py  # Human-in-the-Loop verification gate (y/n)
│   ├── math_evaluator.py     # AST-based safe math expression evaluator
│   ├── file_inspector.py     # Sandboxed workspace file reader & directory lister
│   ├── db_inspector.py       # Read-only SQLite schema and safe query inspector
│   ├── python_runner.py      # Isolated subprocess Python runner with timeout
│   └── tool_registry.py      # Central registration, schema exporter & call parser
├── tests/
│   ├── test_config.py
│   ├── test_agent.py
│   ├── test_memory.py
│   ├── test_knowledge.py
│   ├── test_study_mode.py
│   ├── test_data_cleaner.py
│   ├── test_study_queue.py
│   ├── test_math_formatter.py
│   └── test_tools.py
├── main.py                   # Interactive terminal interface
├── study_markdown.py         # Markdown ingestion script into Knowledge DB
├── study_math.py             # Controlled math ingestion script with 1-hour watchdog
├── requirements.txt
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14 on Windows 11)
- [Ollama](https://ollama.com/) with `qwen3:8b` (accelerated via `OLLAMA_IGPU_ENABLE=1` for AMD Radeon 780M / Vulkan).

### 2. Quickstart
```bash
git clone https://github.com/Titannz/Fogagent.git
cd Fogagent

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run FogAgent
python main.py
```
*(Shortcut: You can type `fogagent` from anywhere in your terminal).*

---

## CLI Commands

| Command | Category | Action |
| :--- | :--- | :--- |
| `youcanstudy` | Study Mode | Enable Study Mode (allow FogAgent to learn new knowledge). |
| `byebye` | Study Mode | Disable Study Mode (stop learning; retains all learned facts). |
| `queue` | Queue | List all pending study items with estimated processing times. |
| `study_now <id>` | Queue | Process a specific deferred study item from the queue. |
| `queue_drop <id>` | Queue | Remove an item from the study queue. |
| `audit` | Quality | Audit database for duplicate topics and low-confidence entries. |
| `delete <id>` | Quality | Permanently delete a specific knowledge entry by ID. |
| `tools` | Tools | List all registered local tools and their risk levels. |
| `eval <expr>` | Tools | Safely evaluate mathematical expressions via AST (`math_evaluator`). |
| `run_py <code>` | Tools | Execute Python code in a timeout-bounded subprocess (`python_runner`). |
| `inspect <path>`| Tools | List directory or inspect text files within workspace (`file_inspector`).|
| `db <name>` | Tools | Inspect local SQLite database schema and run safe SELECT queries (`db_inspector`). |
| `profile` | Memory | View personalized profile, preferences, and hardware constraints. |
| `remember <k>: <v>` | Memory | Store a user preference or fact into Memory. |
| `memories` | Memory | List all stored persistent memories. |
| `knowledge` | Knowledge | List all learned structured knowledge entries. |
| `status` | System | Display model name, GPU offload, and record counts. |
| `exit` / `quit` | System | Exit the CLI. |

---

## Running Tests

Run the complete 49 automated unit tests:
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
- [x] **Phase 6:** Data Quality Pipeline, Loop Control, Workload Estimator & Study Queue.
- [x] ~~**Phase 7:** Autonomous Web Researcher (Removed for safety & offline integrity)~~.
- [x] **Phase 8:** Secure Local Tools (Deterministic local scripts with human verification).
- [ ] **Phase 9:** Autonomous Planning & Task Decomposition DAG.
