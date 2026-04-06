# The Self-Correcting Technical Architect

An autonomous AI-powered system that analyzes requirements, generates code, executes it in a sandbox, validates against specifications, and iteratively improves through self-correction. Built with LangGraph, LangChain, and E2B.

## 🎯 Overview

This system implements a sophisticated multi-agent architecture that combines:

- **Researcher Agent**: Analyzes requirements and generates research-grounded plans
- **Coder Agent**: Generates implementation code and comprehensive test suites
- **Executor Agent**: Runs code in isolated E2B sandboxes for safe execution
- **Reviewer Agent**: Validates code against specifications and provides feedback

The system uses **Test-Driven Development (TDD)** as the core validation mechanism and incorporates a **self-correcting feedback loop** that allows agents to iteratively improve solutions.

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or later (tested with Python 3.14)
- Active API keys for OpenAI, E2B, and Tavily

### Installation

#### 1. Clone the Repository

```bash
cd /Users/asifshaik/coding/genai/Automation/The-Self-Correcting-Technical-Architect
```

#### 2. Run Setup Script (Recommended)

```bash
bash setup.sh
```

This script will:

- Verify Python 3.9+ is installed
- Create a virtual environment
- Install all dependencies from `requirements.txt`
- Verify `.env` file exists

#### 3. Manual Setup (Alternative)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

#### 1. Update `.env` File

Add your API keys to the `.env` file:

```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=gpt-4o

# E2B Sandbox Configuration (Required)
E2B_API_KEY=e2b_your-actual-key-here

# Tavily Search Configuration (Optional)
TAVILY_API_KEY=tvly-your-actual-key-here

# Agent Configuration
MAX_RETRIES=3
CODE_EXECUTION_TIMEOUT=30

# Project Configuration
ENVIRONMENT=development
DEBUG_MODE=false
```

**API Key Sources:**

- **OpenAI**: https://platform.openai.com/account/api-keys
- **E2B**: https://e2b.dev/docs/getting-started/api-key
- **Tavily**: https://tavily.com/ (optional)

#### 2. Verify Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Check Python version
python --version  # Should be 3.10+

# Verify dependencies
python -c "import langgraph, langchain, e2b; print('✅ All dependencies installed!')"
```

## 📖 Usage

### Running the Default Example

```bash
# Activate virtual environment
source venv/bin/activate

# Run the agent
python -m src.main
```

This demonstrates the full workflow with a Fibonacci task.

**Expected Output:**

```
2026-04-06 22:25:49,799 - __main__ - INFO - Initializing agent for task: fib_task_001
2026-04-06 22:25:49,799 - __main__ - INFO - Task: Write a Python function that calculates the Fibonacci sequence
2026-04-06 22:25:49,815 - __main__ - INFO - Starting LangGraph execution...
...
2026-04-06 22:26:39,847 - __main__ - INFO - Agent execution completed. Status: reviewing
2026-04-06 22:26:39,848 - __main__ - INFO - Success: True

=== Final Report ===
[Generated solution report]
```

### Creating Custom Tasks

Edit `src/main.py` to customize the task:

```python
# Around line 193 in src/main.py

EXAMPLE_TASK = "Write a function to validate email addresses"
EXAMPLE_SPEC = """
Requirements:
1. Accept an email string as input
2. Return True if valid, False otherwise
3. Handle RFC 5322 standards
4. Support common TLDs (.com, .org, .net, etc)
5. Include comprehensive error handling
"""

result = asyncio.run(run_agent(EXAMPLE_TASK, EXAMPLE_SPEC, "email_validator_001"))
```

Then run:

```bash
python -m src.main
```

### Viewing Results

Results are saved in two places:

1. **Console Output**: Real-time logs during execution
2. **Memory File**: `logs/experience_memory.json`
   - Successful solutions are automatically saved
   - Enables learning across multiple runs

## 🏗️ System Architecture

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph State Machine                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐     ┌────────┐     ┌──────────┐   ┌─────────┐ │
│  │Researcher│────▶│ Coder  │────▶│ Executor │──▶│Reviewer │ │
│  └──────────┘     └────────┘     └──────────┘   └────┬────┘ │
│       ▲                                                │      │
│       │          ┌──────────────────────────────────┘       │
│       │          │  (Retry if review score < 75)            │
│       └──────────┘  Max 3 attempts                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘

External Services:
├── OpenAI GPT-4o (Research, Code Generation, Review)
├── E2B Sandbox (Safe Code Execution)
├── Tavily Search (Web Research)
└── Local Storage (Memory System)
```

### Agent Responsibilities

#### 1. Researcher Agent

- Analyzes task requirements and technical specifications
- Performs web search for best practices
- Retrieves similar past solutions from memory
- Generates research-grounded implementation plan

#### 2. Coder Agent

- Receives the research plan
- Generates production-ready Python implementation:
  - Type hints
  - PEP 8 compliance
  - Comprehensive docstrings
  - Error handling
- Generates pytest test suite with comprehensive coverage
- Includes detailed explanation

#### 3. Executor Agent

- Spawns isolated E2B sandbox environment
- Executes core implementation
- Runs test suite against implementation
- Captures output, errors, execution time
- Provides detailed execution artifacts

#### 4. Reviewer Agent

- Validates code against technical specification
- Evaluates test results (TDD-first approach)
- Assesses code quality (readability, performance)
- Scores overall compliance (0-100)
- Provides structured feedback
- **Decision**: Accept (score ≥ 75) or Retry (score < 75)

#### 5. Feedback Loop

- Failed solutions trigger retry with feedback
- Maximum 3 retry attempts
- Successful solutions (score ≥ 75) are saved to memory
- Full conversation history enables context-aware improvements

## 📊 Output Interpretation

### Log Levels

- **INFO**: Major workflow steps and results
- **WARNING**: Validation failures and retry triggers
- **ERROR**: Critical failures stopping execution
- **DEBUG**: Detailed execution info (enable with `DEBUG_MODE=true`)

### Review Scoring

```
Score Range     Status      Action
═══════════════════════════════════════════════════
95-100         ✅ PASS     Solution accepted, saved
75-94          ✅ PASS     Solution accepted
60-74          ⚠️  RETRY    Triggers retry (with feedback)
0-59           ❌ FAIL      Critical issues, redesign needed
```

### Success Indicators

**✅ Successful Execution:**

```
Status: reviewing
Success: True
Review Score: 80+
Final code saved to memory
```

**❌ Failed Execution:**

```
Max retries (3) reached
Success: False
Check logs for test output details
```

## 🛠️ Troubleshooting

### Problem: Tests Fail But Core Executes

**Symptoms:**

```
Execution completed - Core: True, Tests: False
Review failed. Score: 60.0/100
```

**Root Cause:**
The generated tests don't properly validate the implementation. This happens when:

- Test assertions are incorrect
- Tests don't cover spec requirements
- Tests have incorrect expected values

**Solution:**

1. Enable debug mode to see test output:

```bash
DEBUG_MODE=true python -m src.main
```

2. The debug logs show test output, look for:
   - Failed assertion details
   - Expected vs actual values
   - Missing test coverage

3. System retries automatically with improved tests (max 3 attempts)
4. If all retries fail, review the spec - it may be ambiguous

### Problem: API Keys Not Found

**Error:**

```
ValidationError: OPENAI_API_KEY - Field required
```

**Solution:**

1. Verify `.env` exists: `ls -la .env`
2. Check key is set: `grep OPENAI_API_KEY .env`
3. Ensure correct format: `OPENAI_API_KEY=sk-proj-xxx` (no spaces)
4. Re-activate venv: `source venv/bin/activate`

### Problem: Model Not Found

**Error:**

```
Error code: 404 - Model 'gpt-4-turbo' does not exist
```

**Solution:**

1. Verify `.env` has correct model: `OPENAI_MODEL=gpt-4o`
2. Check `src/config.py` uses `gpt-4o`
3. Ensure OpenAI account has access to model

### Problem: Rate Limit Exceeded

**Error:**

```
Error code: 429 - You exceeded your current quota
```

**Solution:**

- Upgrade OpenAI account to paid tier
- Or wait for monthly quota reset
- Implement local caching for development

### Problem: Python/Dependency Conflicts

**Error:**

```
Pydantic V1 compatibility error with Python 3.14
```

**Solution:**

- Update all packages: `pip install -r requirements.txt --upgrade`
- Conflicts are usually auto-resolved by pip
- Last resort: Fresh venv `rm -rf venv && bash setup.sh`

## 📚 Project Structure

```
The-Self-Correcting-Technical-Architect/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point and graph builder
│   ├── config.py            # Configuration management
│   ├── state.py             # State definitions (TypedDict)
│   ├── agents/
│   │   ├── researcher.py    # Research and planning
│   │   ├── coder.py         # Code generation
│   │   ├── executor.py      # Sandbox execution
│   │   └── reviewer.py      # Validation and review
│   └── tools/
│       ├── memory.py        # Experience persistence
│       └── search.py        # Web search integration
├── tests/
│   ├── test_main.py
│   ├── test_state.py
│   └── __init__.py
├── logs/
│   └── experience_memory.json    # Saved solutions
├── .env                     # Configuration (git-ignored)
├── .gitignore
├── requirements.txt         # Python dependencies
├── setup.sh                 # Automated setup
└── README.md               # This file
```

## 💾 Memory System

### How It Works

The system learns from every successful solution:

1. **Storage**: Solutions saved to `logs/experience_memory.json`
2. **Retrieval**: Researcher retrieves similar past solutions
3. **Learning**: Past solutions inform implementation planning
4. **Persistence**: Memory survives across multiple runs

### Memory Entry Structure

```json
{
  "task_id": "fib_task_001",
  "task_description": "Write a Python function that calculates the Fibonacci sequence",
  "technical_spec": "Requirements: 1. Accept n... 2. Return list...",
  "final_code": "def fibonacci(n: int) -> List[int]: ...",
  "spec_compliance_score": 95.0,
  "timestamp": "2026-04-06T22:26:39.123456",
  "tags": ["fibonacci", "sequence", "algorithm"]
}
```

## ⚙️ Advanced Configuration

### Custom Memory Location

```bash
MEMORY_FILE_PATH=custom/path/memory.json
```

### Adjust Timeouts

```bash
# Maximum code execution time (seconds)
CODE_EXECUTION_TIMEOUT=60  # Default: 30
```

### Control Retries

```bash
# Maximum retry attempts
MAX_RETRIES=5  # Default: 3
```

### Enable Detailed Logging

```bash
DEBUG_MODE=true  # Enables DEBUG level logging
```

## 🧪 Running Tests

```bash
# Activate venv
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_main.py::test_create_initial_state -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

## 📈 Performance & Costs

### Estimated API Usage Per Task

- **OpenAI**: 5-10 requests (~5,000 tokens each)
  - Cost: $0.05-0.15 per task
- **E2B**: 2-3 sandbox instances
  - Cost: $0.01-0.03 per task

- **Tavily**: 1 optional search request
  - Cost: Varies

**Total estimated: $0.06-0.20 per task with retries**

### Cost Optimization

1. **Reduce retries**: `MAX_RETRIES=2` saves ~$0.05/task
2. **Cache results**: Use memory for similar tasks
3. **Batch processing**: Multiple tasks in sequence
4. **Monitor**: Check OpenAI usage dashboard regularly

## 🚦 Development Roadmap

### Phase 1: Core System ✅ COMPLETE

- Multi-agent LangGraph architecture
- Code generation and E2B sandbox execution
- Test-driven validation
- Memory system

### Phase 2: Enhanced Intelligence 🔄 IN PROGRESS

- Vector database for semantic memory (Pinecone/Chroma)
- Code quality metrics (complexity, coverage)
- Performance profiling
- Improved test evaluation

### Phase 3: Advanced Features 📋 PLANNED

- Human approval gates
- Multi-project learning
- Performance optimization patterns
- Advanced LLM capabilities

### Phase 4: Production Ready

- Comprehensive monitoring
- Rate limiting and queuing
- API versioning
- Scalability improvements

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add feature'`
4. Push branch: `git push origin feature/your-feature`
5. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **LangGraph**: State machine orchestration
- **OpenAI**: GPT-4o language model
- **E2B**: Secure code execution
- **Tavily**: Web search API

## 📧 Support & Resources

**For Issues:**

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs for error details
3. Enable `DEBUG_MODE=true` for detailed output
4. Check GitHub Issues

**Learning Resources:**

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangChain Docs](https://python.langchain.com/)
- [E2B Docs](https://e2b.dev/)
- [OpenAI API](https://platform.openai.com/docs/api-reference)

---

**Last Updated**: April 6, 2026  
**Version**: 1.0.0  
**Status**: Production Ready ✅
