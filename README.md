# JARVIS M3

> **A local-first AI desktop assistant powered by Qwen3, llama.cpp, and tool-based agent orchestration.**

JARVIS M3 is a **local AI desktop assistant** designed to interact with your computer, browser, filesystem, network, and media applications through natural-language commands.

Unlike a traditional chatbot, JARVIS M3 is designed around an **agent + tools architecture**. The language model acts as the reasoning layer, while deterministic Python tools perform actual operations on the host machine.

The project prioritizes:

* Local inference
* Privacy
* Tool-based execution
* Modular architecture
* Computer control
* Browser automation
* Extensibility
* Offline-first operation

---

# Overview

JARVIS M3 is an attempt to build a practical **personal computer agent** rather than another conversational AI application.

The system combines a local Large Language Model with deterministic computer-control tools.

At a high level:

```text
                   ┌─────────────────────┐
                   │       USER          │
                   │ "Open Chrome"       │
                   │ "Play a song"       │
                   │ "Search the web"    │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │   JARVIS M3 CORE    │
                   │                     │
                   │ Intent / Reasoning  │
                   │ Context Management  │
                   │ Tool Selection      │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │      QWEN3-8B       │
                   │    Local LLM        │
                   │                     │
                   │ Tool Calling /      │
                   │ Reasoning           │
                   └──────────┬──────────┘
                              │
                              ▼
              ┌───────────────┴───────────────┐
              │          TOOL LAYER           │
              ├───────────────────────────────┤
              │ Application Control            │
              │ Browser Automation             │
              │ Web Search                     │
              │ Filesystem                     │
              │ Clipboard                      │
              │ Media Control                  │
              │ Network / Wi-Fi                │
              └───────────────┬───────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │   HOST COMPUTER     │
                   │                     │
                   │ Windows / Browser   │
                   │ Files / Network     │
                   │ Applications        │
                   └─────────────────────┘
```

The important architectural principle is:

> **The LLM decides what should happen. Deterministic tools perform the action.**

This separation makes the system easier to extend, debug, and control.

---

# Why JARVIS M3

Most AI assistants follow this model:

```text
User → Cloud API → LLM → Text Response
```

JARVIS M3 follows a different model:

```text
User
  ↓
Local LLM
  ↓
Tool Selection
  ↓
Deterministic Computer Action
  ↓
Tool Result
  ↓
LLM
  ↓
Response
```

This allows the assistant to move from:

> "Here is how you can open Chrome."

to:

> "I opened Chrome."

The assistant therefore operates as an **agent**, not simply a conversational interface.

---

# Core Design Principles

## 1. Local First

The primary LLM runs locally.

User commands do not need to be sent to a remote LLM provider for the core reasoning loop.

This provides:

* Lower dependency on internet connectivity
* Greater privacy
* Local data processing
* Full control over the inference stack
* Ability to customize the model

---

## 2. Tool-Based Architecture

JARVIS does not allow the LLM to directly manipulate the operating system.

Instead:

```text
LLM
 ↓
Tool Call
 ↓
Python Function
 ↓
Operating System
```

For example:

```text
User:
"Open Chrome"

LLM:
open_application("chrome")

Tool:
subprocess / OS operation

Result:
Chrome launched successfully
```

---

## 3. Modular Components

Features are separated into tools/modules.

This makes it possible to add capabilities without rewriting the entire assistant.

For example:

```text
tools/
├── browser.py
├── filesystem.py
├── applications.py
├── clipboard.py
├── media.py
├── network.py
└── search.py
```

A new capability can therefore be introduced as another tool.

---

# Architecture

JARVIS M3 can be divided into five major layers.

```text
┌──────────────────────────────────────────┐
│                 INTERFACE                │
│        CLI / Voice / Future UI           │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│               AGENT CORE                 │
│     Context + Reasoning + Tool Router    │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│               LLM LAYER                  │
│              Qwen3-8B                    │
│              llama.cpp                   │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│                TOOL LAYER                │
│ Browser │ OS │ Files │ Network │ Media   │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│              SYSTEM LAYER                │
│ Windows │ Filesystem │ Browser │ Network │
└──────────────────────────────────────────┘
```

---

# Core Capabilities

## Application Control

JARVIS can interact with installed applications.

Examples:

```text
"Open Chrome"

"Open VS Code"

"Launch Spotify"

"Close Chrome"
```

---

## Browser Control

Browser interaction is handled through automation.

Capabilities include:

* Launching the browser
* Opening URLs
* Searching the web
* Clicking elements
* Typing into pages
* Scrolling
* Navigating pages
* Interacting with dynamic websites

The long-term goal is to provide an autonomous browser agent capable of executing multi-step tasks.

---

## Web Search

JARVIS can perform web searches when a request requires current information.

Example:

```text
"Search for the latest NVIDIA GPU announcement."
```

The assistant can:

```text
User
 ↓
LLM
 ↓
search_web()
 ↓
Search Engine
 ↓
Results
 ↓
LLM
 ↓
Answer
```

---

## Filesystem Operations

JARVIS can interact with local files and directories.

Examples:

```text
"Open my Downloads folder."

"Find the Python project."

"Open the README."

"Show me files in this folder."
```

Filesystem operations should be carefully permission-controlled because they interact directly with user data.

---

## Clipboard

Clipboard operations allow JARVIS to interact with copied text.

Examples:

```text
"Copy this."

"What is currently in my clipboard?"

"Clear the clipboard."
```

---

## Media Control

JARVIS provides media-control functionality.

Supported operations include:

```text
Play
Pause
Resume
Stop
Next
Previous
```

It can also interact with online media platforms through browser automation.

Example:

```text
"Play a song."
```

---

## Network Awareness

JARVIS includes network-related capabilities.

The system can inspect:

* Wi-Fi availability
* Current network state
* Internet connectivity
* Available wireless networks

The project also includes Windows-specific network control functionality where elevated permissions are required.

---

## Wi-Fi Control

JARVIS can interact with Windows networking operations.

Conceptually:

```text
User
 ↓
"Turn Wi-Fi on"
 ↓
LLM
 ↓
network_tool
 ↓
Windows networking subsystem
 ↓
Result
```

Some network operations may require administrator privileges.

---

# Technology Stack

| Component          | Technology                 |
| ------------------ | -------------------------- |
| Language           | Python                     |
| LLM                | Qwen3-8B                   |
| Model Format       | GGUF                       |
| Inference          | llama.cpp                  |
| GPU Acceleration   | CUDA                       |
| Browser Automation | Playwright                 |
| Audio / Media      | pygame                     |
| Platform           | Windows                    |
| Architecture       | Tool-Based AI Agent        |
| Model Server       | llama.cpp server           |
| Environment        | Python virtual environment |

---

# How It Works

Consider:

```text
"Open YouTube and play music."
```

JARVIS does not simply generate a text response.

The execution flow is approximately:

```text
1. User sends command
        ↓
2. JARVIS receives command
        ↓
3. Local Qwen model analyzes intent
        ↓
4. Model determines required tools
        ↓
5. Tool execution begins
        ↓
6. Browser is opened
        ↓
7. YouTube is navigated
        ↓
8. Search/action is performed
        ↓
9. Tool returns result
        ↓
10. LLM receives result
        ↓
11. JARVIS reports completion
```

This creates a feedback loop:

```text
              ┌─────────────┐
              │    User     │
              └──────┬──────┘
                     ↓
              ┌─────────────┐
              │     LLM     │
              └──────┬──────┘
                     ↓
              ┌─────────────┐
              │    Tool     │
              └──────┬──────┘
                     ↓
              ┌─────────────┐
              │ Tool Result │
              └──────┬──────┘
                     ↓
              ┌─────────────┐
              │     LLM     │
              └──────┬──────┘
                     ↓
                User Response
```

---

# Project Structure

The project is designed around modular components.

A representative structure is:

```text
JARVIS-M3/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── agent.py
│   │   ├── llm.py
│   │   ├── router.py
│   │   └── context.py
│   │
│   ├── tools/
│   │   ├── applications.py
│   │   ├── browser.py
│   │   ├── filesystem.py
│   │   ├── clipboard.py
│   │   ├── media.py
│   │   ├── network.py
│   │   └── search.py
│   │
│   ├── services/
│   │   ├── audio.py
│   │   └── browser_service.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── utils/
│       ├── logger.py
│       └── helpers.py
│
├── models/
│   └── assistant.gguf
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

The exact structure may evolve as the agent architecture becomes more sophisticated.

---

# Requirements

## Hardware

Recommended configuration:

* NVIDIA RTX GPU
* 8 GB+ VRAM
* 16 GB+ system RAM
* Modern multi-core CPU
* SSD storage

JARVIS M3 has been designed and tested around an NVIDIA RTX 4060 Laptop GPU with 8 GB VRAM.

---

## Software

Required:

* Windows 10/11
* Python 3.12+
* NVIDIA GPU drivers
* CUDA-compatible environment
* Git

Recommended:

* Visual Studio Build Tools
* VS Code
* PowerShell
* Git

---

# Installation

## 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>

cd JARVIS-M3
```

---

## 2. Create Virtual Environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

You should see:

```text
(.venv)
```

in your terminal.

---

## 3. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

---

## 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

# Model Setup

JARVIS M3 uses a local GGUF model.

The current architecture is designed around:

```text
Qwen3-8B
      ↓
GGUF
      ↓
llama.cpp
      ↓
CUDA
      ↓
Local inference
```

Place the model inside:

```text
models/
```

Example:

```text
models/
└── assistant.gguf
```

The model does not need to be committed to Git because model files can be several gigabytes in size.

Add them to `.gitignore`:

```gitignore
models/*.gguf
```

---

# Running the LLM Server

JARVIS communicates with the local model through the llama.cpp server.

The default endpoint is:

```text
http://127.0.0.1:8080/v1
```

The architecture therefore looks like:

```text
JARVIS Python Application
          │
          │ HTTP
          ▼
┌──────────────────────┐
│   llama.cpp server   │
│                      │
│      Qwen3-8B        │
│                      │
│      CUDA GPU        │
└──────────────────────┘
```

---

# Configuration

Configuration should be stored through environment variables rather than hard-coded values.

Example:

```env
LLM_BASE_URL=http://127.0.0.1:8080/v1
LLM_MODEL=assistant
LLM_REQUEST_TIMEOUT=90
```

Recommended configuration structure:

```text
.env
```

Do not commit:

```text
.env
```

to Git.

Add:

```gitignore
.env
```

---

# Running JARVIS M3

Start the llama.cpp server first.

Then:

```powershell
python -m app.main
```

Expected startup:

```text
JARVIS M3
Local AI Assistant
------------------

LLM: Qwen3-8B
Backend: llama.cpp
Mode: Local
Status: Ready
```

You can then issue commands.

Example:

```text
You:
Open Chrome
```

JARVIS:

```text
Opening Chrome.
```

---

# Command Examples

## Applications

```text
Open Chrome
```

```text
Open VS Code
```

```text
Launch calculator
```

---

## Browser

```text
Open YouTube
```

```text
Search YouTube for lo-fi music
```

```text
Open GitHub
```

```text
Search the web for Python decorators
```

---

## Files

```text
Open Downloads
```

```text
Find my project folder
```

```text
Open the README file
```

---

## Media

```text
Play
```

```text
Pause
```

```text
Resume
```

```text
Next
```

```text
Previous
```

```text
Stop
```

---

## Network

```text
Check my internet connection
```

```text
Show available Wi-Fi networks
```

```text
Check Wi-Fi status
```

---

# Tool System

The tool system is the most important architectural component of JARVIS M3.

Instead of allowing the model to execute arbitrary Python code, the model is given a controlled set of tools.

Example:

```python
{
    "name": "open_application",
    "description": "Open an installed application",
    "parameters": {
        "application": "string"
    }
}
```

The model can produce a structured tool request:

```text
open_application(
    application="chrome"
)
```

The Python runtime executes the function.

This gives the architecture a clear separation:

```text
┌──────────────┐
│     LLM      │
│              │
│ decides      │
└──────┬───────┘
       │
       │ structured request
       ▼
┌──────────────┐
│ Tool Router  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Python Tool  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Operating    │
│ System       │
└──────────────┘
```

---

# Browser Automation

JARVIS uses Playwright for browser automation.

The browser agent is intended to provide capabilities such as:

```text
Observe
 ↓
Understand
 ↓
Locate element
 ↓
Click
 ↓
Type
 ↓
Navigate
 ↓
Observe result
 ↓
Continue
```

This enables multi-step browser tasks.

Example:

```text
"Search YouTube for Imagine Dragons and play the first result."
```

Possible execution:

```text
Open YouTube
      ↓
Search "Imagine Dragons"
      ↓
Inspect results
      ↓
Locate first video
      ↓
Click
      ↓
Verify playback
```

The long-term objective is to make this workflow autonomous while maintaining strict tool boundaries.

---

# Agent Execution Model

JARVIS M3 is moving toward an agent loop similar to:

```text
THINK
  ↓
PLAN
  ↓
ACT
  ↓
OBSERVE
  ↓
EVALUATE
  ↓
ACT AGAIN
  ↓
COMPLETE
```

For example:

```text
Goal:
"Find the latest Python release and open the official page."

        ↓

Plan:
1. Search web
2. Identify official Python result
3. Open result

        ↓

Action:
search_web()

        ↓

Observation:
Search results returned

        ↓

Action:
open_url()

        ↓

Observation:
Official Python page loaded

        ↓

Complete
```

This is fundamentally different from a simple chatbot request/response system.

---

# Local LLM Architecture

The LLM stack is:

```text
                 JARVIS M3
                     │
                     ▼
             OpenAI-compatible
                  API layer
                     │
                     ▼
              llama.cpp server
                     │
                     ▼
                 GGUF model
                     │
                     ▼
                 Qwen3-8B
                     │
                     ▼
                 CUDA GPU
```

This allows the application layer to communicate with the local model using a standardized API interface.

The current configuration uses:

```text
Base URL:
http://127.0.0.1:8080/v1

Model:
assistant
```

---

# Why llama.cpp?

llama.cpp provides a practical inference layer for running quantized LLMs locally.

JARVIS M3 uses it because the project requires:

* Local inference
* GGUF support
* GPU acceleration
* Low-level inference control
* OpenAI-compatible server access
* Ability to run without a cloud LLM dependency

---

# Privacy

JARVIS M3 is designed around a local-first philosophy.

The primary reasoning model runs on the user's machine.

This means sensitive local operations can remain local:

```text
User Input
    ↓
Local LLM
    ↓
Local Tool
    ↓
Local Machine
```

However, privacy depends on the specific tool being executed.

For example, a web-search tool necessarily communicates with an external service.

Therefore:

> **Local LLM does not automatically mean zero network communication.**

Each tool should explicitly document whether it communicates externally.

---

# Security

Because JARVIS has access to the operating system, security is a major concern.

The assistant should **never blindly execute arbitrary model-generated code**.

Avoid architectures such as:

```python
exec(llm_output)
```

or:

```python
eval(llm_output)
```

These create an extremely dangerous execution boundary.

Instead:

```text
LLM
 ↓
Validated tool call
 ↓
Allowed parameters
 ↓
Tool
 ↓
Operation
```

---

# Permission Model

Future versions should implement permission levels.

Example:

```text
SAFE
 ├── Open application
 ├── Search web
 ├── Read clipboard
 └── Read files

CONFIRMATION REQUIRED
 ├── Delete file
 ├── Move files
 ├── Install software
 ├── Change system configuration
 └── Send external messages

ADMINISTRATIVE
 ├── Modify firewall
 ├── Change network configuration
 ├── Modify system services
 └── Other elevated operations
```

This prevents a reasoning mistake from becoming a system-level mistake.

---

# Logging

Agent systems are difficult to debug without observability.

JARVIS M3 should maintain structured logs for:

```text
User input
LLM request
LLM response
Selected tool
Tool arguments
Tool result
Execution time
Errors
```

Example:

```text
[USER]
Open Chrome

[LLM]
Tool: open_application

[TOOL]
application=chrome

[RESULT]
success=true

[AGENT]
Task completed
```

This makes failures traceable.

---

# Error Handling

Tools should never crash the entire agent.

Instead of:

```python
tool()
```

the architecture should conceptually behave like:

```python
try:
    result = tool()
except Exception as error:
    result = {
        "success": False,
        "error": str(error)
    }
```

The result can then be returned to the agent.

Example:

```json
{
  "success": false,
  "error": "Chrome executable not found"
}
```

The LLM can then decide what to do next.

---

# Development

Clone the project:

```powershell
git clone <YOUR_REPOSITORY_URL>
cd JARVIS-M3
```

Create environment:

```powershell
python -m venv .venv
```

Activate:

```powershell
.venv\Scripts\activate
```

Install:

```powershell
pip install -r requirements.txt
```

Run:

```powershell
python -m app.main
```

---

# Testing

Tests should be separated into multiple layers.

## Unit Tests

Test individual tools:

```text
test_browser.py
test_filesystem.py
test_network.py
test_media.py
```

---

## Integration Tests

Test:

```text
LLM
 ↓
Tool Router
 ↓
Tool
```

---

## End-to-End Tests

Test complete user workflows:

```text
User command
 ↓
Agent
 ↓
Tool
 ↓
External application
 ↓
Result
```

E2E tests should be used carefully for destructive operations.

---

# Troubleshooting

## LLM server unavailable

Error:

```text
Connection refused
```

Check that llama.cpp server is running.

Verify:

```text
http://127.0.0.1:8080
```

---

## CUDA problems

Check NVIDIA driver:

```powershell
nvidia-smi
```

Verify that the GPU is detected.

---

## Python environment problems

Check:

```powershell
python --version
```

and:

```powershell
pip --version
```

Make sure the virtual environment is active.

---

## Playwright browser missing

Install the required browser:

```powershell
playwright install
```

---

## Permission errors

Some Windows operations require administrator privileges.

Do not solve permission errors by automatically running the entire assistant as administrator.

Instead, isolate elevated operations behind explicit permission boundaries.

---

# Future Architecture

The long-term JARVIS M3 architecture is expected to evolve toward:

```text
                       ┌───────────────┐
                       │     USER      │
                       └───────┬───────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Interaction Layer │
                    │                    │
                    │ Voice / Text / UI  │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │    Agent Core      │
                    │                    │
                    │ Planner            │
                    │ Memory             │
                    │ Context            │
                    │ Reasoning          │
                    └─────────┬──────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
        ┌────────────┐ ┌────────────┐ ┌────────────┐
        │ Browser    │ │ Computer   │ │ Filesystem │
        │ Agent      │ │ Control    │ │ Agent      │
        └────────────┘ └────────────┘ └────────────┘
               │              │              │
               └──────────────┼──────────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │     Tool Layer     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │     Operating      │
                    │      System        │
                    └────────────────────┘
```

---

# Memory Architecture

A future memory system can be separated into:

```text
Short-Term Memory
        │
        ├── Current conversation
        ├── Current task
        └── Tool results

Long-Term Memory
        │
        ├── User preferences
        ├── Frequently used applications
        ├── Previous tasks
        └── Persistent knowledge
```

The memory system should not blindly store every interaction.

Memory needs:

* Relevance filtering
* User control
* Data retention rules
* Secure storage
* Retrieval mechanisms
* Deletion capabilities

---

# Agent vs Chatbot

The fundamental distinction in JARVIS M3 is:

### Chatbot

```text
Input
 ↓
LLM
 ↓
Text
```

### Agent

```text
Goal
 ↓
LLM
 ↓
Plan
 ↓
Tool
 ↓
Environment
 ↓
Observation
 ↓
LLM
 ↓
Next Action
 ↓
...
 ↓
Goal Complete
```

JARVIS M3 is designed for the second architecture.

---

# Design Philosophy

The project follows a simple principle:

> **Language models should reason. Deterministic software should execute.**

The LLM is probabilistic.

Operating-system operations are not.

Therefore, critical operations should remain behind deterministic interfaces.

Bad architecture:

```text
LLM → arbitrary Python code → OS
```

Better architecture:

```text
LLM
 ↓
Structured tool call
 ↓
Validation
 ↓
Permission check
 ↓
Deterministic function
 ↓
OS
```

This separation is one of the core engineering principles behind JARVIS M3.


---

## JARVIS M3

**Local Intelligence.
Tool-Based Execution.
Computer-Level Agency.**
