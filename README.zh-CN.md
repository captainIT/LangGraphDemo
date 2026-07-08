# LangGraph Demo

**中文** | [English](README.md)

> **最好的多 Agent 实践项目**：LangGraph 工作流、MCP 工具服务与 A2A Agent 端点集成于同一 FastAPI 应用，适合入门与团队内部分享。

## 项目目的

本项目是一个 **LangGraph + MCP + A2A 学习样板**，涵盖：

- **LangGraph** — 状态图、Reducer、检查点、条件路由、ReAct Agent
- **MCP** — stdio 工具 Server、发现与调用（`langchain-mcp-adapters`）
- **A2A** — Agent Card、JSON-RPC 消息与任务生命周期（`a2a-sdk`）

所有能力共用同一套 FastAPI 分层（`api / service / transport / schemas`），业务逻辑保持精简。

后续的正式业务项目可以**以此仓库作为起始模版**——保留上述分层与集成方式，在此基础上扩展 Agent、工作流与业务逻辑，而无需从零搭建工程骨架。

### 能力概览

| 模块 | 内容 | 主要入口 |
|------|------|----------|
| **LangGraph** | 有状态工作流与图演示 | `POST /api/v1/agents/workflow`、`/demo/*` |
| **LangChain Agent** | 5 个简单 LLM Agent + 工具调用 | `POST /api/v1/agents/run` |
| **MCP** | 3 个 stdio Server，工具发现与调用 | `GET /api/v1/mcp/tools`、`/demo/full-flow` |
| **A2A** | 2 个协议兼容 Agent（`echo`、`qa`） | Agent Card + `/api/v1/a2a/demo/full-flow` |

> **MCP 与 A2A**：MCP 面向 *工具* 暴露给 LLM/Agent 运行时；A2A 面向 *Agent* 实现跨框架互通。本项目同时包含两者。

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

按需编辑 `.env`，常用变量如下：

| 变量 | 是否必填 | 默认值 | 说明 |
|------|----------|--------|------|
| `OPENAI_API_KEY` | LLM 相关路由需要 | — | OpenAI 或兼容服务的 API Key |
| `OPENAI_MODEL` | 否 | `gpt-4o-mini` | 模型名称 |
| `OPENAI_BASE_URL` | 否 | — | 兼容 API 地址（如 DeepSeek、Azure） |
| `APP_NAME` | 否 | `LangGraph Demo` | FastAPI 应用标题 |
| `SERVER_HOST` | 否 | `127.0.0.1` | Uvicorn/FastAPI 绑定地址 |
| `SERVER_PORT` | 否 | `8000` | Uvicorn/FastAPI 绑定端口 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |
| `MCP_TIMEOUT_SECONDS` | 否 | `30` | MCP 发现 / 调用超时 |
| `MCP_TOOL_NAME_PREFIX` | 否 | `true` | 工具名是否带 server 前缀 |
| `A2A_PUBLIC_BASE_URL` | 否 | `http://127.0.0.1:8000` | 写入 A2A Agent Card 的公网地址 |
| `A2A_TIMEOUT_SECONDS` | 否 | `60` | A2A 拉 Card / 发消息超时 |

未配置 `OPENAI_API_KEY` 时，LangGraph LLM 演示、`qa` A2A Agent 及大部分 `/agents/run` 不可用；`echo` A2A Agent 与 MCP 演示仍可运行。
请确保 `A2A_PUBLIC_BASE_URL` 与 `SERVER_HOST` + `SERVER_PORT` 一致，避免 Agent Card 自调用地址不匹配。

## 4. 运行

```bash
uv run uvicorn app.main:app --reload
```

也可使用（读取配置中的 `SERVER_HOST` / `SERVER_PORT`）：

```bash
uv run python -m app.main
```

若已执行 `source .venv/bin/activate`，也可直接运行 `uvicorn app.main:app --reload`。

- **OpenAPI 文档**：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)（含 A2A 协议路由）
- **HTTP 测试**：`http_test/api_requests.http`（VS Code / Cursor REST Client）

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

## 7. A2A（Agent-to-Agent Protocol）

本项目通过官方 [`a2a-sdk`](https://github.com/a2aproject/a2a-python) 暴露 **2 个内置 A2A Demo Agent**，并挂载到 FastAPI：

| A2A Agent | 路径 | 说明 |
|-----------|------|------|
| `echo` | `/a2a/echo/` | 回显用户输入，演示标准 A2A 任务生命周期 |
| `qa` | `/a2a/qa/` | LLM 问答 Agent（需配置 `OPENAI_API_KEY`） |

每个 Agent 在其路径下发布 **Agent Card**（`/.well-known/agent-card.json`），并通过 **JSON-RPC** 接收 `message/send` 请求。

分层位置：

- `app/transport/a2a/executors/` — `AgentExecutor` 实现
- `app/transport/a2a/registry.py` — Agent 注册与示例消息
- `app/transport/a2a/server_setup.py` — 在 FastAPI 上挂载 A2A 路由
- `app/transport/a2a_client.py` — A2A Client 传输层
- `app/service/a2a_service.py` — 发现、发消息、全流程测试编排
- `app/api/a2a_router.py` — HTTP 测试接口

请配置 `A2A_PUBLIC_BASE_URL`（默认 `http://127.0.0.1:8000`），以便 Agent Card 与客户端自调用解析正确。若使用其他 host/port，测试前请先更新该值。

各 Executor 遵循 A2A 任务生命周期：`submit → working → artifact → completed`（见 `app/transport/a2a/task_helpers.py`）。

### 全流程测试接口

`POST /api/v1/a2a/demo/full-flow` 会依次执行：

1. 解析已挂载的 Agent
2. 拉取各 Agent Card
3. 通过 A2A Client 发送示例消息
4. 返回 `steps` 追踪与 `messages` 结果

单消息测试：`POST /api/v1/a2a/demo/message`

## 8. API 端点

### 健康检查与 Agent

- `GET /health`
- `GET /api/v1/agents`
- `POST /api/v1/agents/run`
- `POST /api/v1/agents/run-with-trace`（工具 Agent，含 tool_calls 追踪）
- `POST /api/v1/agents/workflow` **（LangGraph 协作工作流）**
- `POST /api/v1/agents/demo/checkpoint` **（LangGraph 检查点 + `add_messages`）**
- `POST /api/v1/agents/demo/conditional-route` **（LangGraph 条件边）**
- `POST /api/v1/agents/demo/react-agent` **（LangGraph `create_react_agent`）**
- `WS /api/v1/agents/ws`

### 工具

- `GET /api/v1/tools`
- `POST /api/v1/tools`

### MCP

- `GET /api/v1/mcp/servers`
- `GET /api/v1/mcp/tools`
- `POST /api/v1/mcp/tools/invoke`
- `POST /api/v1/mcp/demo/full-flow` **（MCP 全流程测试）**
- `POST /api/v1/mcp/demo/server/{server_name}` **（单 MCP Server 全流程测试）**

### A2A

- `GET /api/v1/a2a/agents`
- `GET /api/v1/a2a/agents/{agent_name}/card`
- `POST /api/v1/a2a/demo/message` **（A2A 单消息测试）**
- `POST /api/v1/a2a/demo/full-flow` **（A2A 全流程测试）**
- `GET /a2a/echo/.well-known/agent-card.json` **（A2A Agent Card — echo）**
- `POST /a2a/echo/` **（A2A JSON-RPC — echo）**
- `GET /a2a/qa/.well-known/agent-card.json` **（A2A Agent Card — qa）**
- `POST /a2a/qa/` **（A2A JSON-RPC — qa）**

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

A2A echo Agent 单消息测试：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/a2a/demo/message" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "echo", "input_text": "hello a2a"}'
```

A2A 全流程测试（拉取 Agent Card → 发送示例消息）：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/a2a/demo/full-flow" \
  -H "Content-Type: application/json" \
  -d '{"use_sample_messages": true}'
```

WebSocket 流式请求体示例：

```json
{
  "agent_type": "qa_agent",
  "input_text": "Explain what LangGraph is in simple words."
}
```

## 9. 统一错误响应

所有路由返回统一包裹结构（`ApiResponse`）。请求失败时，全局异常处理会映射为：

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

常见 `message` 值：

- `request_failed`（HTTP 异常，如 400/404）
- `validation_failed`（请求体/参数校验失败）
- `internal_server_error`（服务端未预期异常）

## 10. 项目结构

```text
app/
  api/              # FastAPI 路由（agents、tools、mcp、a2a）
  service/          # 业务服务层
  transport/        # LLM / MCP / A2A 通信层
    mcp/servers/    # 独立 stdio MCP Server 脚本
    mcp/registry.py # MCP Server 注册表
    a2a/executors/  # A2A AgentExecutor 实现
    a2a/registry.py # A2A Agent 注册表
    *_client.py     # MCP / A2A Client 传输层
    *_graph.py      # LangGraph 状态图定义
  schemas/          # 请求/响应 Pydantic 模型
  utils/            # 日志、工具函数
http_test/
  api_requests.http # REST Client 冒烟测试
static/
  index.html        # 可选 UI，访问 /ui
```
