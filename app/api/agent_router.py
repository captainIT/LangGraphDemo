import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.config import Settings, get_settings
from app.schemas.agent import (
    AgentRunRequest,
    AgentRunResult,
    AgentRunWithTraceResult,
    AgentType,
    AgentWorkflowRequest,
    AgentWorkflowResult,
    ToolCallTrace,
)
from app.schemas.common import ApiResponse
from app.service.agent_service import AgentService
from app.transport.llm_client import LlmClient

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
logger = logging.getLogger(__name__)


def get_agent_service(settings: Annotated[Settings, Depends(get_settings)]) -> AgentService:
    llm_client = LlmClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    return AgentService(llm_client=llm_client)


@router.get("", response_model=ApiResponse)
async def list_agents(
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> ApiResponse:
    return ApiResponse(data={"agents": service.list_agents()})


@router.post("/run", response_model=ApiResponse)
async def run_agent(
    payload: AgentRunRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> ApiResponse:
    try:
        output_text = await service.run_agent(
            agent_type=payload.agent_type, input_text=payload.input_text
        )
        result = AgentRunResult(agent_type=payload.agent_type, output_text=output_text)
        return ApiResponse(data=result.model_dump())
    except Exception as exc:
        logger.exception("agent execution failed", extra={"agent_type": payload.agent_type.value})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run agent",
        ) from exc


@router.post("/run-with-trace", response_model=ApiResponse)
async def run_agent_with_trace(
    payload: AgentRunRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> ApiResponse:
    if payload.agent_type != AgentType.tool_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="run-with-trace currently supports tool_agent only",
        )

    try:
        output_text, tool_calls = await service.run_tool_agent_with_trace(payload.input_text)
        result = AgentRunWithTraceResult(
            agent_type=payload.agent_type,
            output_text=output_text,
            tool_calls=[ToolCallTrace(**item) for item in tool_calls],
        )
        return ApiResponse(data=result.model_dump())
    except Exception as exc:
        logger.exception("agent run with trace failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run agent with trace",
        ) from exc


@router.post("/workflow", response_model=ApiResponse)
async def run_workflow(
    payload: AgentWorkflowRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> ApiResponse:
    try:
        steps, output_text = await service.run_collaborative_workflow(payload.input_text)
        result = AgentWorkflowResult(steps=steps, output_text=output_text)
        return ApiResponse(data=result.model_dump())
    except Exception as exc:
        logger.exception("workflow execution failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run collaborative workflow",
        ) from exc


@router.websocket("/ws")
async def stream_agent(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        agent_type_value = str(payload.get("agent_type", "qa_agent"))
        input_text = str(payload.get("input_text", "")).strip()

        if not input_text:
            await websocket.send_json({"event": "error", "message": "input_text is required"})
            await websocket.close(code=1008)
            return

        if agent_type_value not in {item.value for item in AgentType}:
            await websocket.send_json({"event": "error", "message": "invalid agent_type"})
            await websocket.close(code=1008)
            return

        settings = get_settings()
        service = AgentService(
            llm_client=LlmClient(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        )
        await websocket.send_json({"event": "start", "agent_type": agent_type_value})

        async for chunk in service.stream_agent(
            agent_type=AgentType(agent_type_value),
            input_text=input_text,
        ):
            await websocket.send_json({"event": "chunk", "content": chunk})

        await websocket.send_json({"event": "end"})
        await websocket.close(code=1000)
    except WebSocketDisconnect:
        logger.info("websocket disconnected by client")
    except Exception as exc:
        logger.exception("websocket streaming failed")
        try:
            await websocket.send_json({"event": "error", "message": "stream failed"})
            await websocket.close(code=1011)
        except Exception:
            logger.exception("websocket close after error failed")
        raise exc
