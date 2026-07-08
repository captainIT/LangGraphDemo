# LangGraph Demo

[中文](README.zh-CN.md) | **English**

> **A minimal LangGraph hands-on project**: run the full loop of **state graph → compile → async invoke** with very little business code—ideal for getting started and sharing within a team.

## Project Purpose

This repository is a **LangGraph learning and practice** starter: it demonstrates core capabilities—state graphs, nodes and edges, reducers, checkpointing, conditional routing, ReAct agents, and more—with minimal business logic, plus a clear FastAPI layering (`api / service / transport / schemas`).

Future production projects can **use this repo as a starting template**—keep the layered structure and LangGraph integration patterns, then extend agents, workflows, and business logic without scaffolding from scratch.

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

Update `OPENAI_API_KEY` in `.env`.

## 4. Run

```bash
uv run uvicorn app.main:app --reload
```

After `source .venv/bin/activate`, you can run `uvicorn app.main:app --reload` instead if you prefer a classic venv workflow.

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

## 7. API Endpoints

- `GET /health`
- `GET /api/v1/agents`
- `POST /api/v1/agents/run`
- `POST /api/v1/agents/run-with-trace` (tool agent with tool_calls trace)
- `POST /api/v1/agents/workflow` **(LangGraph collaborative workflow)**
- `POST /api/v1/agents/demo/checkpoint` **(LangGraph checkpoint + `add_messages`)**
- `POST /api/v1/agents/demo/conditional-route` **(LangGraph conditional edges)**
- `POST /api/v1/agents/demo/react-agent` **(LangGraph `create_react_agent`)**
- `WS /api/v1/agents/ws`
- `GET /api/v1/tools`
- `POST /api/v1/tools`
- `GET /api/v1/mcp/servers`
- `GET /api/v1/mcp/tools`
- `POST /api/v1/mcp/tools/invoke`
- `POST /api/v1/mcp/demo/full-flow` **(MCP full-flow test)**
- `POST /api/v1/mcp/demo/server/{server_name}` **(single MCP server full-flow test)**

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

WebSocket stream payload example:

```json
{
  "agent_type": "qa_agent",
  "input_text": "Explain what LangGraph is in simple words."
}
```

## 8. Project Structure

```text
app/
  api/          # FastAPI routers
  service/      # Business services
  transport/    # LLM / MCP communication layer
    mcp/        # MCP server modules and registry
  schemas/      # Request/response models
  utils/        # Utility helpers
```
