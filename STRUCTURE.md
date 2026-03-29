# Self-Correcting Technical Architect - Project Structure

## Complete Directory Tree

```
Automation/
│
├── 📄 README.md                          # Comprehensive project documentation
├── 📄 BOILERPLATE_SUMMARY.md             # Phase 1 deliverables summary
├── 📄 requirements.txt                   # Exact pinned dependencies (v0.2.8+)
├── 📄 Makefile                           # 25+ development commands
├── 📄 setup.sh                           # Automated environment setup
├── 📄 .env.example                       # Environment variables template
├── 📄 .gitignore                         # Git ignore rules
│
├── 📁 src/                               # Main source code
│   ├── 📄 __init__.py
│   ├── 📄 main.py                        # Entry point & LangGraph orchestrator
│   ├── 📄 state.py                       # TypedDict state definitions
│   ├── 📄 config.py                      # Configuration & settings (Pydantic)
│   │
│   ├── 📁 agents/                        # Agent node implementations
│   │   ├── 📄 __init__.py
│   │   ├── 📄 researcher.py              # Node 1: Requirement analysis
│   │   ├── 📄 coder.py                   # Node 2: Code generation
│   │   ├── 📄 executor.py                # Node 3: Sandbox execution
│   │   └── 📄 reviewer.py                # Node 4: Spec validation
│   │
│   └── 📁 tools/                         # Utility functions (expandable)
│       └── 📄 __init__.py
│
└── 📁 tests/                             # Test suite
    ├── 📄 __init__.py
    ├── 📄 test_state.py                  # State definition tests
    └── 📄 test_main.py                   # Graph structure tests
```

## File Descriptions

### Root Level

| File                       | Purpose                                                               | Status      |
| -------------------------- | --------------------------------------------------------------------- | ----------- |
| **README.md**              | Comprehensive documentation with usage, architecture, troubleshooting | ✅ Complete |
| **BOILERPLATE_SUMMARY.md** | This summary file and Phase 1 deliverables checklist                  | ✅ Complete |
| **requirements.txt**       | Exact pinned versions of all dependencies                             | ✅ Complete |
| **Makefile**               | 25+ commands for setup, test, lint, run                               | ✅ Complete |
| **setup.sh**               | Automated environment initialization script                           | ✅ Complete |
| **.env.example**           | Template for environment variables                                    | ✅ Complete |
| **.gitignore**             | Git ignore rules for Python/IDE/logs                                  | ✅ Complete |

### src/ - Source Code

| File                     | Lines | Purpose                                                 | Status      |
| ------------------------ | ----- | ------------------------------------------------------- | ----------- |
| **main.py**              | ~210  | LangGraph state machine, node definitions, run_agent()  | ✅ Complete |
| **state.py**             | ~85   | TypedDict definitions for AgentState, messages, results | ✅ Complete |
| **config.py**            | ~55   | Pydantic settings, environment variable loading         | ✅ Complete |
| **agents/researcher.py** | ~65   | Researcher node: requirement analysis                   | ✅ Complete |
| **agents/coder.py**      | ~80   | Coder node: code generation                             | ✅ Complete |
| **agents/executor.py**   | ~100  | Executor node: sandbox execution with E2B               | ✅ Complete |
| **agents/reviewer.py**   | ~140  | Reviewer node: spec validation with scoring             | ✅ Complete |

### tests/ - Test Suite

| File              | Lines | Purpose                                   | Status      |
| ----------------- | ----- | ----------------------------------------- | ----------- |
| **test_state.py** | ~55   | State structure and type validation tests | ✅ Complete |
| **test_main.py**  | ~40   | Graph structure and initialization tests  | ✅ Complete |

---

## File Statistics

```
Total Files: 20
Total Lines: ~1,800

Breakdown:
├── Python Code: 9 files, ~800 lines
├── Tests: 2 files, ~95 lines
├── Configuration: 4 files, ~200 lines
├── Documentation: 3 files, ~700 lines
└── Setup/Tooling: 2 files, ~5 lines
```

---

## Development Workflow

### 1. Initial Setup

```bash
bash setup.sh              # Automated setup
# OR manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure API Keys

```bash
# Edit .env and add:
OPENAI_API_KEY=sk-...
E2B_API_KEY=...
```

### 3. Development

```bash
make format              # Format code
make lint                # Check code quality
make test                # Run tests
make run                 # Execute agent
```

---

## Key Features by File

### main.py ✅

- LangGraph state machine builder
- Node registration and edge definition
- Conditional retry logic
- Example usage with asyncio
- Type-hinted throughout

### state.py ✅

- AgentState TypedDict (15 fields)
- AgentMessage with metadata
- ExecutionResult with artifacts
- ReviewCriteria checklist

### config.py ✅

- Pydantic v2 settings management
- Environment variable validation
- Type-safe configuration
- Singleton instance pattern

### researcher.py ✅

- LLM-based requirement analysis
- Plan generation
- Message history tracking
- Status updates

### coder.py ✅

- Code generation with temperature 0.3
- Type hints and docstring inclusion
- Code history preservation
- Retry counter increment

### executor.py ✅

- E2B sandbox integration
- 30-second timeout protection
- Mock execution fallback
- Execution result capture

### reviewer.py ✅

- LLM-based code review
- Score extraction from text
- Issue identification
- Go/no-go decision logic

---

## Module Dependencies

```
main.py
├── langgraph.graph (StateGraph, END)
├── langchain_openai (ChatOpenAI)
├── langchain_core (HumanMessage, AIMessage)
├── state.py (AgentState)
├── config.py (settings)
└── agents/* (researcher, coder, executor, reviewer)

state.py
└── typing (TypedDict)

config.py
├── pydantic (BaseSettings)
├── pydantic_settings (BaseSettings)
└── os

agents/
├── researcher.py → langchain_openai, config
├── coder.py → langchain_openai, config
├── executor.py → e2b_code_interpreter (optional)
└── reviewer.py → langchain_openai, config

tests/
├── test_state.py → pytest, state.py
└── test_main.py → pytest, main.py, state.py
```

---

## Execution Flow Diagram

```
User calls run_agent()
│
├─→ build_graph()                 # Create LangGraph state machine
│   ├─→ Researcher node          # Analyze requirements
│   ├─→ Coder node               # Generate code
│   ├─→ Executor node            # Run in sandbox
│   ├─→ Reviewer node            # Validate against spec
│   └─→ Conditional edges        # Retry or finish
│
├─→ create_initial_state()        # Initialize AgentState
│
└─→ graph.ainvoke(state)          # Execute state machine
    │
    ├─→ Researcher transforms:    state['status'] = 'coding'
    ├─→ Coder transforms:         state['status'] = 'executing'
    ├─→ Executor transforms:      state['status'] = 'reviewing'
    ├─→ Reviewer transforms:      state['success'] = True/False
    │
    ├─→ If success:               RETURN final_state
    └─→ If failure & retries:     LOOP to Coder
```

---

## Requirements Explained

### Core Framework (4 packages)

- **langgraph** - Graph-based state machine orchestration
- **langchain** - LLM interaction framework
- **langchain-openai** - OpenAI-specific integrations
- **langchain-core** - Base classes and types

### Execution (1 package)

- **e2b-code-interpreter** - Secure sandboxed Python execution

### Configuration (2 packages)

- **pydantic** - Data validation with type hints
- **python-dotenv** - Load environment variables from .env

### Development (5 packages)

- **pytest** - Testing framework
- **black** - Code formatter
- **pylint** - Code linter
- **mypy** - Static type checker
- **pytest-asyncio** - Async test support

---

## Environment Variables

| Variable               | Required | Default     | Purpose                    |
| ---------------------- | -------- | ----------- | -------------------------- |
| OPENAI_API_KEY         | ✅       | -           | OpenAI authentication      |
| E2B_API_KEY            | ✅       | -           | E2B sandbox authentication |
| OPENAI_MODEL           | ❌       | gpt-4-turbo | Model selection            |
| MAX_RETRIES            | ❌       | 3           | Max retry attempts         |
| CODE_EXECUTION_TIMEOUT | ❌       | 30          | Sandbox timeout (seconds)  |
| ENVIRONMENT            | ❌       | development | Environment type           |
| DEBUG_MODE             | ❌       | false       | Enable debug logging       |

---

## Make Commands Summary

```
make help                   Show all commands
make setup                  Complete environment setup
make install                Install dependencies
make install-dev            Install + dev tools
make test                   Run tests with coverage
make lint                   Check code quality
make format                 Format code with Black
make clean                  Remove generated files
make run                    Execute the agent
```

Total: 25+ commands available

---

## Ready for Production

This boilerplate is designed for solo developer productivity with:

✅ **Minimal Setup** - One command: `bash setup.sh`  
✅ **Type Safety** - Full type hints with MyPy support  
✅ **Error Handling** - Comprehensive try-catch and logging  
✅ **Modularity** - Easy to extend with new nodes  
✅ **Testing** - Pytest structure ready to use  
✅ **Documentation** - README + docstrings throughout  
✅ **Automation** - Makefile with 25+ commands  
✅ **Security** - Sandboxed execution, env variables

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Date**: March 25, 2026
