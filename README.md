# LangGraph Demo

[中文](README.zh-CN.md) | **English**

> **A minimal multi-agent hands-on project**: LangGraph workflows, MCP tool servers, and A2A agent endpoints in one FastAPI app—ideal for learning and team sharing.

## Project Purpose

This repository is a **LangGraph + MCP + A2A learning starter**. It demonstrates:

- **LangGraph** — state graphs, reducers, checkpointing, conditional routing, ReAct agents
- **MCP** — stdio tool servers, discovery, and invocation via `langchain-mcp-adapters`
- **A2A** — Agent Cards, JSON-RPC messaging, and task lifecycle via `a2a-sdk`

All features share the same FastAPI layering (`api / service / transport / schemas`) with minimal business logic.

Future production projects can **use this repo as a starting template**—keep the layered structure and integration patterns, then extend agents, workflows, and business logic without scaffolding from scratch.

### Capability overview

| Area | What you get | Key entry points |
|------|--------------|------------------|
| **LangGraph** | Stateful workflows & graph demos | `POST /api/v1/agents/workflow`, `/demo/*` |
| **LangChain agents** | 5 simple LLM agents + tool calling | `POST /api/v1/agents/run` |
| **MCP** | 3 stdio servers, tool discovery & invoke | `GET /api/v1/mcp/tools`, `/demo/full-flow` |
| **A2A** | 2 protocol-compliant agents (`echo`, `qa`) | Agent Card + `/api/v1/a2a/demo/full-flow` |

> **MCP vs A2A**: MCP exposes *tools* for LLM/agent runtimes; A2A exposes *agents* for cross-framework agent-to-agent communication. This project includes both.

---

A minimal FastAPI + LangGraph demo project with 5 simple agents:

- `qa_agent`: General Q&A assistant
- `summary_agent`: Text summarizer
- `translate_agent`: Chinese to English translator
- `planner_agent`: Task planner
- `tool_agent`: Function-calling agent

Built-in function calls for `tool_agent`:

- `get_current_utc_time`
- `add_numbers`
- `count_words`
- `slugify_text`

## 1. Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (package manager / runner)
- OpenAI API key

## 2. Install

From the project root (uses `uv.lock` and creates `.venv` if needed):

```bash
uv sync
```

## 3. Configure

```bash
cp .env.example .env
```

Edit `.env` as needed. Common variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | For LLM routes | — | API key for OpenAI or compatible providers |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model name |
| `OPENAI_BASE_URL` | No | — | OpenAI-compatible base URL (e.g. DeepSeek, Azure) |
| `APP_NAME` | No | `LangGraph Demo` | FastAPI app title |
| `SERVER_HOST` | No | `127.0.0.1` | Uvicorn/FastAPI bind host |
| `SERVER_PORT` | No | `8000` | Uvicorn/FastAPI bind port |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `MCP_TIMEOUT_SECONDS` | No | `30` | MCP discovery / invocation timeout |
| `MCP_TOOL_NAME_PREFIX` | No | `true` | Prefix tool names with server name |
| `A2A_PUBLIC_BASE_URL` | No | `http://127.0.0.1:8000` | Public URL embedded in A2A Agent Cards |
| `A2A_TIMEOUT_SECONDS` | No | `60` | A2A card fetch / message timeout |

Without `OPENAI_API_KEY`, LangGraph LLM demos, `qa` A2A agent, and most `/agents/run` routes are unavailable; `echo` A2A agent and MCP demos still work.
Keep `A2A_PUBLIC_BASE_URL` aligned with `SERVER_HOST` + `SERVER_PORT` to avoid Agent Card self-call mismatches.

## 4. Run

```bash
uv run uvicorn app.main:app --reload
```

This also works (uses `SERVER_HOST` / `SERVER_PORT` from settings):

```bash
uv run python -m app.main
```

After `source .venv/bin/activate`, you can run `uvicorn app.main:app --reload` instead if you prefer a classic venv workflow.

- **OpenAPI docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (includes A2A protocol routes)
- **HTTP tests**: `http_test/api_requests.http` (VS Code / Cursor REST Client)

## 5. LangGraph in this project

### Which APIs use LangGraph?

| Method & path | LangGraph feature |
|---------------|-------------------|
| **`POST /api/v1/agents/workflow`** | Linear `StateGraph`, reducers (`operator.add` on `steps`), `compile()`, `ainvoke()`. |
| **`POST /api/v1/agents/demo/checkpoint`** | **Checkpointing**: `compile(checkpointer=InMemorySaver())`, multi-turn state keyed by `thread_id` in `configurable`. |
| **`POST /api/v1/agents/demo/conditional-route`** | **Conditional edges**: `add_conditional_edges` routes to different nodes (math vs general) without a checkpoint. |
| **`POST /api/v1/agents/demo/react-agent`** | **Prebuilt ReAct**: `create_react_agent` tool loop (same demo tools as `tool_agent`). |

Other routes (`/run`, `/run-with-trace`, `/ws`, `/tools`, etc.) use **LangChain** (`langchain_core` / `langchain_openai`) only; they do **not** run a LangGraph `CompiledStateGraph` (except the demo routes above).

### How the main workflow works (short)

1. **State** — A `TypedDict` (`WorkflowState` in `app/transport/collaborative_workflow_graph.py`) describes the data carried through the graph: user input, routing metadata, primary agent id, merged `steps`, and final `output_text`.
2. **Graph** — `StateGraph(WorkflowState)` registers async **nodes** (`route` → `primary` → optional summarize → optional translate) and **edges** from `START` … `END`.
3. **Reducers** — Fields like `steps` use `Annotated[list[str], operator.add]` so multiple nodes can append trace entries without overwriting each other; that is LangGraph’s channel/reducer pattern on the state schema.
4. **Compile & run** — `graph.compile()` returns a runnable. The service calls **`await graph.ainvoke({"input_text": ..., "steps": []})`**, which walks the fixed pipeline, merges partial node returns into state, and returns the final state (used to build `steps` + `output_text` in the JSON response).

### Demo routes (short)

- **Checkpoint** — `app/transport/checkpoint_chat_graph.py`: message list uses `add_messages`; the process-wide `InMemorySaver` from `app/transport/checkpoint_store.py` keeps history per `thread_id` across requests until the server restarts.
- **Conditional route** — `app/transport/conditional_branch_graph.py`: a router node plus `add_conditional_edges` picks the next node from user text heuristics.
- **ReAct** — `app/transport/react_prebuilt_graph.py`: wraps `create_react_agent`; `LangGraphDemoService` in `app/service/langgraph_demo_service.py` runs `ainvoke` and shapes the JSON response.

For the collaborative workflow node logic, open `app/transport/collaborative_workflow_graph.py`.

## 6. MCP (Model Context Protocol)

This project ships **3 stdio MCP server modules**, wired through `langchain-mcp-adapters` `MultiServerMCPClient` for tool discovery and invocation:

| MCP Server | Tools |
|------------|-------|
| `math` | `add_numbers`, `multiply_numbers` |
| `time` | `get_current_utc_time` |
| `text` | `count_words`, `slugify_text` |

Layering:

- `app/transport/mcp/servers/` — standalone MCP server scripts (runnable via `python ..._server.py` with stdio)
- `app/transport/mcp/registry.py` — server registry and stdio connection config
- `app/transport/mcp_client.py` — MCP client transport
- `app/service/mcp_service.py` — discovery, invocation, full-flow orchestration
- `app/api/mcp_router.py` — HTTP test endpoints

With default `MCP_TOOL_NAME_PREFIX=true`, tool names are prefixed by server (e.g. `math_add_numbers`) to avoid collisions across servers.

### Full-flow test endpoint

`POST /api/v1/mcp/demo/full-flow` runs:

1. Resolve and connect all (or selected) MCP servers
2. Discover tools
3. Invoke sample tools per server
4. Return `steps` trace and `invocations` results

Per-server test: `POST /api/v1/mcp/demo/server/{server_name}`

## 7. A2A (Agent-to-Agent Protocol)

This project exposes **2 built-in A2A demo agents** using the official [`a2a-sdk`](https://github.com/a2aproject/a2a-python) with FastAPI route mounting:

| A2A Agent | Path | Description |
|-----------|------|-------------|
| `echo` | `/a2a/echo/` | Echo user input via standard A2A task lifecycle |
| `qa` | `/a2a/qa/` | LLM Q&A agent (requires `OPENAI_API_KEY`) |

Each agent publishes an **Agent Card** at `/.well-known/agent-card.json` under its path and accepts **JSON-RPC** `message/send` requests.

Layering:

- `app/transport/a2a/executors/` — `AgentExecutor` implementations
- `app/transport/a2a/registry.py` — agent registry and sample messages
- `app/transport/a2a/server_setup.py` — mount A2A routes on FastAPI
- `app/transport/a2a_client.py` — A2A client transport
- `app/service/a2a_service.py` — discovery, messaging, full-flow orchestration
- `app/api/a2a_router.py` — HTTP test endpoints

Set `A2A_PUBLIC_BASE_URL` (default `http://127.0.0.1:8000`) so Agent Cards and client self-calls resolve correctly. If you run on another host/port, update this value before testing.

Each executor follows the A2A task lifecycle: `submit → working → artifact → completed` (see `app/transport/a2a/task_helpers.py`).

### Full-flow test endpoint

`POST /api/v1/a2a/demo/full-flow` runs:

1. Resolve mounted agents
2. Fetch each Agent Card
3. Send a sample message via the A2A client
4. Return `steps` trace and `messages` results

Direct message test: `POST /api/v1/a2a/demo/message`

## 8. API Endpoints

### Health & agents

- `GET /health`
- `GET /api/v1/agents`
- `POST /api/v1/agents/run`
- `POST /api/v1/agents/run-with-trace` (tool agent with tool_calls trace)
- `POST /api/v1/agents/workflow` **(LangGraph collaborative workflow)**
- `POST /api/v1/agents/demo/checkpoint` **(LangGraph checkpoint + `add_messages`)**
- `POST /api/v1/agents/demo/conditional-route` **(LangGraph conditional edges)**
- `POST /api/v1/agents/demo/react-agent` **(LangGraph `create_react_agent`)**
- `WS /api/v1/agents/ws`

### Tools

- `GET /api/v1/tools`
- `POST /api/v1/tools`

### MCP

- `GET /api/v1/mcp/servers`
- `GET /api/v1/mcp/tools`
- `POST /api/v1/mcp/tools/invoke`
- `POST /api/v1/mcp/demo/full-flow` **(MCP full-flow test)**
- `POST /api/v1/mcp/demo/server/{server_name}` **(single MCP server full-flow test)**

### A2A

- `GET /api/v1/a2a/agents`
- `GET /api/v1/a2a/agents/{agent_name}/card`
- `POST /api/v1/a2a/demo/message` **(A2A message test)**
- `POST /api/v1/a2a/demo/full-flow` **(A2A full-flow test)**
- `GET /a2a/echo/.well-known/agent-card.json` **(A2A Agent Card — echo)**
- `POST /a2a/echo/` **(A2A JSON-RPC — echo)**
- `GET /a2a/qa/.well-known/agent-card.json` **(A2A Agent Card — qa)**
- `POST /a2a/qa/` **(A2A JSON-RPC — qa)**

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "summary_agent",
    "input_text": "LangGraph helps you build stateful, multi-step LLM workflows."
  }'
```

Function call request example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "tool_agent",
    "input_text": "Please add 12.5 and 7.3, then generate a slug for: LangGraph Tool Calling Demo"
  }'
```

Function call with LLM trace example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run-with-trace" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "tool_agent",
    "input_text": "What time is it in UTC? Also count words in: LangGraph tool call demo"
  }'
```

Direct tool call (without LLM) example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "add_numbers",
    "arguments": {"a": 12.5, "b": 7.3}
  }'
```

Workflow request:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Please create a short launch plan for an AI chatbot and output in English."
  }'
```

LangGraph checkpoint demo (call twice with the same `thread_id` to continue the thread):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/demo/checkpoint" \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "demo-user-1", "input_text": "My name is Alex. Remember it in one short sentence."}'

curl -X POST "http://127.0.0.1:8000/api/v1/agents/demo/checkpoint" \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "demo-user-1", "input_text": "What is my name?"}'
```

Conditional-route demo (math branch if the text looks like a calculation):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/demo/conditional-route" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Calculate 12.5 + 7.3 and explain briefly."}'
```

Prebuilt ReAct demo:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/demo/react-agent" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "What UTC time is it? Then add 10 and 32."}'
```

MCP full-flow test (connect → discover tools → sample invocations):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/mcp/demo/full-flow" \
  -H "Content-Type: application/json" \
  -d '{"include_tool_invocations": true}'
```

MCP single tool invocation (prefixed name by default):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/mcp/tools/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "math_add_numbers",
    "arguments": {"a": 12.5, "b": 7.3}
  }'
```

A2A echo agent message test:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/a2a/demo/message" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "echo", "input_text": "hello a2a"}'
```

A2A full-flow test (fetch Agent Cards → send sample messages):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/a2a/demo/full-flow" \
  -H "Content-Type: application/json" \
  -d '{"use_sample_messages": true}'
```

WebSocket stream payload example:

```json
{
  "agent_type": "qa_agent",
  "input_text": "Explain what LangGraph is in simple words."
}
```

## 9. Unified Error Response

All routers return a consistent envelope (`ApiResponse`). For failed requests, global exception handlers map errors to:

```json
{
  "success": false,
  "message": "request_failed",
  "data": {},
  "error": {
    "code": "bad_request",
    "detail": "Detailed reason"
  }
}
```

Common `message` values:

- `request_failed` (HTTP exceptions such as 400/404)
- `validation_failed` (request body/parameter validation errors)
- `internal_server_error` (unexpected server failures)

## 10. Project Structure

```text
app/
  api/              # FastAPI routers (agents, tools, mcp, a2a)
  service/          # Business services
  transport/        # LLM / MCP / A2A communication layer
    mcp/servers/    # Standalone stdio MCP server scripts
    mcp/registry.py # MCP server registry
    a2a/executors/  # A2A AgentExecutor implementations
    a2a/registry.py # A2A agent registry
    *_client.py     # MCP / A2A client transports
    *_graph.py      # LangGraph state graph definitions
  schemas/          # Request/response Pydantic models
  utils/            # Logging, tool helpers
http_test/
  api_requests.http # REST Client smoke tests
static/
  index.html        # Optional UI at /ui
```
