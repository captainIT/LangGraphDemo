# LangChain Multi Agent Demo

A minimal FastAPI + LangChain demo project with 5 simple agents:

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
- OpenAI API key

## 2. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 3. Configure

```bash
cp .env.example .env
```

Update `OPENAI_API_KEY` in `.env`.

## 4. Run

```bash
uvicorn app.main:app --reload
```

## 5. API Endpoints

- `GET /health`
- `GET /api/v1/agents`
- `POST /api/v1/agents/run`
- `POST /api/v1/agents/run-with-trace` (tool agent with tool_calls trace)
- `POST /api/v1/agents/workflow`
- `WS /api/v1/agents/ws`
- `GET /api/v1/tools`
- `POST /api/v1/tools`

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "summary_agent",
    "input_text": "LangChain makes it easier to build LLM-powered applications."
  }'
```

Function call request example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "tool_agent",
    "input_text": "Please add 12.5 and 7.3, then generate a slug for: LangChain Tool Calling Demo"
  }'
```

Function call with LLM trace example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agents/run-with-trace" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "tool_agent",
    "input_text": "What time is it in UTC? Also count words in: LangChain tool call demo"
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

WebSocket stream payload example:

```json
{
  "agent_type": "qa_agent",
  "input_text": "Explain what LangChain is in simple words."
}
```

## 6. Project Structure

```text
app/
  api/          # FastAPI routers
  service/      # Business services
  transport/    # LLM communication layer
  schemas/      # Request/response models
  utils/        # Utility helpers
```
