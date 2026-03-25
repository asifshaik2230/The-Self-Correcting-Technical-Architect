# The Self-Correcting Technical Architect

An autonomous agent system that uses LangGraph for stateful orchestration and E2B sandboxed execution to autonomously plan, code, execute, and review solutions with self-correction capabilities.

## 🎯 Architecture Overview

The system implements a **Plan → Code → Execute → Review** feedback loop using LangGraph's state machine:

```
┌──────────────┐
│  Researcher  │  Analyzes requirements and creates implementation plan
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Coder     │  Generates production-ready code based on plan
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Executor   │  Runs code in E2B sandboxed environment
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Reviewer   │  Validates code against technical specification
└──────┬───────┘
       │
       ├─→ Success? → END (return final code)
       │
       └─→ Failure? → Retry (max 3 attempts) → Loop back to Coder
```

## 📁 Project Structure

```
Automation/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point and graph builder
│   ├── state.py                # TypedDict definitions for agent state
│   ├── config.py               # Configuration and settings management
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── researcher.py       # Plan & analysis node
│   │   ├── coder.py            # Code generation node
│   │   ├── executor.py         # Sandbox execution node
│   │   └── reviewer.py         # Spec validation node
│   └── tools/
│       └── __init__.py         # (Future: utility functions)
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_state.py
├── requirements.txt            # Python dependencies with exact versions
├── setup.sh                    # Environment initialization script
├── Makefile                    # Build and development commands
├── .env.example                # Template for environment variables
├── README.md                   # This file
└── .gitignore
```

## 🔧 Technology Stack

### Core Framework

- **LangGraph** (0.2.8): Stateful graph-based orchestration
- **LangChain** (0.1.14): LLM interaction framework
- **LangChain-OpenAI** (0.1.8): OpenAI API integration

### Code Execution

- **E2B Code Interpreter** (1.0.3): Secure sandboxed code execution

### Data & Config

- **Pydantic** (2.6.3): Data validation and settings
- **Python-dotenv** (1.0.0): Environment variable management

### Development

- **Pytest** (7.4.4): Testing framework
- **Black** (24.1.1): Code formatting
- **Pylint** (3.0.3): Code linting
- **MyPy** (1.8.0): Static type checking

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key
- E2B API key (for sandboxed execution)

### Setup

1. **Clone and navigate to the project:**

   ```bash
   cd /Users/asifshaik/coding/genai/Automation
   ```

2. **Run the setup script (recommended):**

   ```bash
   bash setup.sh
   ```

   Or manually:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Configure API keys in `.env`:**

   ```bash
   # Edit .env and add:
   OPENAI_API_KEY=sk-your-key-here
   E2B_API_KEY=your-e2b-key-here
   ```

4. **Verify the setup:**
   ```bash
   make check  # Runs linting and format checks
   ```

## 📖 Usage

### Run with Default Task

```bash
python -m src.main
```

### Run a Custom Task

```python
import asyncio
from src.main import run_agent

async def main():
    result = await run_agent(
        task_description="Write a function that finds prime numbers",
        technical_spec="""
        Requirements:
        1. Accept a parameter n
        2. Return list of primes up to n
        3. Handle n < 2 edge case
        4. Optimize for performance
        """,
        task_id="prime_finder_001"
    )
    print(f"Success: {result['success']}")
    print(f"Final Code:\n{result['final_code']}")

asyncio.run(main())
```

### Using Make Commands

```bash
# Environment setup
make setup          # Full environment initialization
make venv           # Create virtual environment
make env            # Create .env from template

# Installation
make install        # Install dependencies
make install-dev    # Install dev tools

# Development
make format         # Format code with Black
make lint           # Run linting checks
make test           # Run tests with coverage
make clean          # Remove generated files

# Execution
make run            # Run the agent
make run-example    # Run with example task

# Utilities
make check          # Run all code checks
make all            # Full setup, install, test, lint
```

## 🔄 Agent State Flow

### State Dictionary (TypedDict: `AgentState`)

```python
AgentState = {
    # Identifiers
    'task_id': str,
    'task_description': str,
    'technical_spec': str,

    # Messages and history
    'messages': List[AgentMessage],  # Full conversation history

    # Code tracking
    'code': str,                      # Current implementation
    'code_history': List[str],        # Previous versions
    'code_explanation': str,

    # Execution results
    'execution_logs': List[ExecutionResult],
    'last_execution': Optional[ExecutionResult],

    # Validation
    'validation_errors': List[str],
    'review_feedback': str,
    'spec_compliance_score': float,   # 0.0 to 1.0

    # Control flow
    'retry_count': int,
    'max_retries': int,
    'status': str,                    # planning|coding|executing|reviewing|completed|failed

    # Outputs
    'final_code': Optional[str],
    'final_report': Optional[str],
    'success': bool,
}
```

## 🔐 Node Responsibilities

### Researcher Node

- **Input**: Task description, technical specification
- **Process**: Analyzes requirements, creates implementation strategy
- **Output**: Structured plan with components, algorithms, challenges
- **Next**: Coder

### Coder Node

- **Input**: Research plan, specification, previous feedback
- **Process**: Generates production-ready Python code with:
  - Type hints
  - Error handling
  - Comprehensive docstrings
  - PEP 8 compliance
- **Output**: Generated source code
- **Next**: Executor

### Executor Node

- **Input**: Generated code
- **Process**: Executes code in E2B sandbox with:
  - Timeout protection (30s default)
  - Output capture (stdout/stderr)
  - Execution time tracking
- **Output**: Execution results and artifacts
- **Next**: Reviewer

### Reviewer Node

- **Input**: Code, execution results, specification
- **Process**: Validates against spec:
  - Correctness check
  - Spec compliance
  - Error handling coverage
  - Performance assessment
  - Code quality review
- **Output**: Review score (0-100), issues list, compliance status
- **Decision**: Success (END) or Retry (max 3)
- **Next**: Coder (retry) or END

## 🛡️ Error Handling & Retry Logic

1. **Automatic Retries**: If review fails, the agent retries code generation (max 3 attempts)
2. **Timeout Protection**: E2B sandbox has 30-second execution timeout
3. **Validation Errors**: Captured and included in retry feedback to the coder
4. **State Preservation**: Full message history allows context-aware retries

## ⚙️ Configuration

### Environment Variables (`.env`)

```
# OpenAI Configuration
OPENAI_API_KEY=sk-...           # Required: OpenAI API key
OPENAI_MODEL=gpt-4-turbo        # Model selection (default: gpt-4-turbo)

# E2B Configuration
E2B_API_KEY=...                 # Required: E2B sandbox API key

# Agent Configuration
MAX_RETRIES=3                   # Max retry attempts (default: 3)
CODE_EXECUTION_TIMEOUT=30       # Timeout in seconds (default: 30s)

# Optional: LangChain Tracing
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false

# Project Settings
ENVIRONMENT=development         # development|production
DEBUG_MODE=false               # Enable debug logging
```

## 📊 Monitoring & Logging

Logs are written to stdout with the format:

```
2026-03-25 10:30:45,123 - src.agents.researcher - INFO - Researcher node: Plan generated successfully
```

Log files can be captured by redirecting output:

```bash
python -m src.main > logs/run_$(date +%s).log 2>&1
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_main.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run without coverage (faster)
make test-quick
```

## 📋 Development Workflow

1. **Code changes**: Make edits in `src/`
2. **Format**: `make format`
3. **Lint**: `make lint`
4. **Test**: `make test`
5. **Run**: `make run`

Or run all at once:

```bash
make check
```

## 🔍 Type Safety

The project uses:

- **TypedDict** for structured state definitions
- **Type hints** throughout codebase
- **MyPy** static type checking

Check types:

```bash
mypy src/ --ignore-missing-imports
```

## 📚 Key Concepts

### LangGraph State Machine

- **Nodes**: Functions that process state (researcher, coder, executor, reviewer)
- **Edges**: Transitions between nodes
- **Conditional Edges**: Routes based on state (review pass/fail)
- **State**: Dictionary shared across all nodes

### E2B Sandbox

- **Isolation**: Code runs in isolated container
- **Security**: No filesystem or network access by default
- **Results**: Captures stdout, stderr, artifacts

### TypedDict

- Provides IDE autocomplete for state dictionaries
- Type hints without runtime overhead
- Prevents typos in state key access

## 🚨 Troubleshooting

### "ImportError: No module named 'langgraph'"

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "OPENAI_API_KEY not found"

```bash
cp .env.example .env
# Edit .env and add your key
```

### "E2B sandbox timeout"

Increase timeout in `.env`:

```
CODE_EXECUTION_TIMEOUT=60
```

### "Code execution always succeeds (mock mode)"

E2B not installed. Install it:

```bash
pip install e2b-code-interpreter
```

## 📝 Notes for Solo Development

This architecture is optimized for solo developers:

- **Minimal dependencies**: Only essential libraries
- **Clear separation**: Each node handles one responsibility
- **Easy to extend**: Add new nodes without changing existing ones
- **Type safety**: Prevents bugs through static typing
- **Testing**: Comprehensive test structure ready to use

## 🔮 Future Enhancements

- [ ] Add persistent state storage (database)
- [ ] Implement parallel execution for independent tasks
- [ ] Add memory/vector store for knowledge persistence
- [ ] Support multiple LLM providers (Claude, Gemini)
- [ ] Add structured output parsing (Pydantic validators)
- [ ] Web UI for task submission and monitoring
- [ ] Metrics and performance dashboards

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is a solo dev project, but feel free to fork and customize!

---

**Created**: March 2026  
**Status**: Production-Ready (Phase 1)  
**Maintained by**: Your Name
