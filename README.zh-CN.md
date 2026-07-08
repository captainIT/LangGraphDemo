# LangGraph Demo

**中文** | [English](README.md)

> **最好的 LangGraph 简单实践项目**：用极少的业务代码把 LangGraph 的「状态图 → 编译 → 异步执行」跑通，适合入门与团队内部分享。

## 项目目的

本项目旨在成为 **LangGraph 学习与实战** 的入门样板：用最小化的业务代码跑通 LangGraph 的核心能力（状态图、节点与边、Reducer、检查点、条件路由、ReAct Agent 等），并配合 FastAPI 提供清晰的 API 分层结构（`api / service / transport / schemas`）。

后续的正式业务项目可以**以此仓库作为起始模版**——保留上述分层与 LangGraph 集成方式，在此基础上扩展 Agent、工作流与业务逻辑，而无需从零搭建工程骨架。

---

基于 FastAPI + LangGraph 的最小化示例项目，内置 5 个简单 Agent：

- `qa_agent`：通用问答助手
- `summary_agent`：文本摘要
- `translate_agent`：中译英
- `planner_agent`：任务规划
- `tool_agent`：函数调用 Agent

`tool_agent` 内置工具：

- `get_current_utc_time`
- `add_numbers`
- `count_words`
- `slugify_text`

## 1. 环境要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)（包管理 / 运行器）
- OpenAI API Key

## 2. 安装

在项目根目录执行（使用 `uv.lock`，必要时自动创建 `.venv`）：

```bash
uv sync
```

## 3. 配置

```bash
cp .env.example .env
```

在 `.env` 中填写 `OPENAI_API_KEY`。

## 4. 运行

```bash
uv run uvicorn app.main:app --reload
```

若已执行 `source .venv/bin/activate`，也可直接运行 `uvicorn app.main:app --reload`。

## 5. 本项目中的 LangGraph

### 哪些 API 使用了 LangGraph？

| 方法与路径 | LangGraph 特性 |
|-----------|----------------|
| **`POST /api/v1/agents/workflow`** | 线性 `StateGraph`、Reducer（`steps` 字段使用 `operator.add`）、`compile()`、`ainvoke()` |
| **`POST /api/v1/agents/demo/checkpoint`** | **检查点**：`compile(checkpointer=InMemorySaver())`，通过 `configurable` 中的 `thread_id` 维护多轮状态 |
| **`POST /api/v1/agents/demo/conditional-route`** | **条件边**：`add_conditional_edges` 按输入路由到不同节点（数学 vs 通用），无需检查点 |
| **`POST /api/v1/agents/demo/react-agent`** | **预置 ReAct**：`create_react_agent` 工具循环（与 `tool_agent` 使用相同演示工具） |

其他路由（`/run`、`/run-with-trace`、`/ws`、`/tools` 等）仅使用 **LangChain**（`langchain_core` / `langchain_openai`），**不**运行 LangGraph 的 `CompiledStateGraph`（上述演示路由除外）。

### 主工作流如何运作（简述）

1. **状态** — `TypedDict`（`app/transport/collaborative_workflow_graph.py` 中的 `WorkflowState`）描述图中流转的数据：用户输入、路由元数据、主 Agent ID、合并后的 `steps`、最终 `output_text`。
2. **图** — `StateGraph(WorkflowState)` 注册异步**节点**（`route` → `primary` → 可选 summarize → 可选 translate）及从 `START` 到 `END` 的**边**。
3. **Reducer** — 如 `steps` 使用 `Annotated[list[str], operator.add]`，多个节点可追加追踪记录而不互相覆盖；这是 LangGraph 在状态模式上的 channel/reducer 机制。
4. **编译与运行** — `graph.compile()` 返回可执行对象；服务层调用 **`await graph.ainvoke({"input_text": ..., "steps": []})`**，沿固定流水线执行，将各节点返回值合并进状态，最终得到完整状态（用于构建 JSON 响应中的 `steps` 与 `output_text`）。

### 演示路由（简述）

- **检查点** — `app/transport/checkpoint_chat_graph.py`：消息列表使用 `add_messages`；`app/transport/checkpoint_store.py` 中的进程级 `InMemorySaver` 按 `thread_id` 跨请求保留历史，直至服务重启。
- **条件路由** — `app/transport/conditional_branch_graph.py`：路由节点配合 `add_conditional_edges`，根据用户文本启发式选择下一节点。
- **ReAct** — `app/transport/react_prebuilt_graph.py`：封装 `create_react_agent`；`app/service/langgraph_demo_service.py` 中的 `LangGraphDemoService` 执行 `ainvoke` 并组装 JSON 响应。

协作工作流的节点逻辑见 `app/transport/collaborative_workflow_graph.py`。

## 6. MCP（Model Context Protocol）

本项目内置 3 个 **stdio MCP Server** 模块，并通过 `langchain-mcp-adapters` 的 `MultiServerMCPClient` 完成工具发现与调用：

| MCP Server | 工具 |
|------------|------|
| `math` | `add_numbers`, `multiply_numbers` |
| `time` | `get_current_utc_time` |
| `text` | `count_words`, `slugify_text` |

分层位置：

- `app/transport/mcp/servers/` — 独立 MCP Server 脚本（可单独 `python ..._server.py` 以 stdio 运行）
- `app/transport/mcp/registry.py` — Server 注册与 stdio 连接配置
- `app/transport/mcp_client.py` — MCP Client 传输层
- `app/service/mcp_service.py` — 发现、调用、全流程测试编排
- `app/api/mcp_router.py` — HTTP 测试接口

默认 `MCP_TOOL_NAME_PREFIX=true`，工具名会带 server 前缀（如 `math_add_numbers`），避免多 Server 重名冲突。

### 全流程测试接口

`POST /api/v1/mcp/demo/full-flow` 会依次执行：

1. 解析并连接所有（或指定）MCP Server
2. 发现工具列表
3. 对每个 Server 执行示例工具调用
4. 返回 `steps` 追踪与 `invocations` 结果

单 Server 测试：`POST /api/v1/mcp/demo/server/{server_name}`

## 7. API 端点

- `GET /health`
- `GET /api/v1/agents`
- `POST /api/v1/agents/run`
- `POST /api/v1/agents/run-with-trace`（工具 Agent，含 tool_calls 追踪）
- `POST /api/v1/agents/workflow` **（LangGraph 协作工作流）**
- `POST /api/v1/agents/demo/checkpoint` **（LangGraph 检查点 + `add_messages`）**
- `POST /api/v1/agents/demo/conditional-route` **（LangGraph 条件边）**
- `POST /api/v1/agents/demo/react-agent` **（LangGraph `create_react_agent`）**
- `WS /api/v1/agents/ws`
- `GET /api/v1/tools`
- `POST /api/v1/tools`
- `GET /api/v1/mcp/servers`
- `GET /api/v1/mcp/tools`
- `POST /api/v1/mcp/tools/invoke`
- `POST /api/v1/mcp/demo/full-flow` **（MCP 全流程测试）**
- `POST /api/v1/mcp/demo/server/{server_name}` **（单 MCP Server 全流程测试）**

基础请求示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "summary_agent",
    "input_text": "LangGraph helps you build stateful, multi-step LLM workflows."
  }'
```

函数调用示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "tool_agent",
    "input_text": "Please add 12.5 and 7.3, then generate a slug for: LangGraph Tool Calling Demo"
  }'
```

带 LLM 追踪的函数调用示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run-with-trace" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "tool_agent",
    "input_text": "What time is it in UTC? Also count words in: LangGraph tool call demo"
  }'
```

直接调用工具（不经过 LLM）示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "add_numbers",
    "arguments": {"a": 12.5, "b": 7.3}
  }'
```

工作流请求示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Please create a short launch plan for an AI chatbot and output in English."
  }'
```

LangGraph 检查点演示（使用相同 `thread_id` 调用两次以延续会话）：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/demo/checkpoint" \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "demo-user-1", "input_text": "My name is Alex. Remember it in one short sentence."}'

curl -X POST "http://127.0.0.1:8000/api/v1/agents/demo/checkpoint" \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "demo-user-1", "input_text": "What is my name?"}'
```

条件路由演示（文本像计算题时走数学分支）：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/demo/conditional-route" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Calculate 12.5 + 7.3 and explain briefly."}'
```

预置 ReAct 演示：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/demo/react-agent" \
  -H "Content-Type: application/json" \
  -d '{"input_text": "What UTC time is it? Then add 10 and 32."}'
```

MCP 全流程测试（连接 → 发现工具 → 示例调用）：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/mcp/demo/full-flow" \
  -H "Content-Type: application/json" \
  -d '{"include_tool_invocations": true}'
```

MCP 单工具调用（默认带 server 前缀）：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/mcp/tools/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "math_add_numbers",
    "arguments": {"a": 12.5, "b": 7.3}
  }'
```

WebSocket 流式请求体示例：

```json
{
  "agent_type": "qa_agent",
  "input_text": "Explain what LangGraph is in simple words."
}
```

## 8. 项目结构

```text
app/
  api/          # FastAPI 路由
  service/      # 业务服务层
  transport/    # LLM / MCP 通信层
    mcp/        # MCP Server 模块与注册表
  schemas/      # 请求/响应模型
  utils/        # 工具函数
```
