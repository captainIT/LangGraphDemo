import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.error_utils import raise_bad_request, raise_internal_server_error
from app.config import Settings, get_settings
from app.schemas.a2a import A2aFullFlowRequest, A2aMessageRequest
from app.schemas.common import ApiResponse
from app.service.a2a_service import A2aService
from app.transport.a2a_client import A2aClientTransport

router = APIRouter(prefix="/api/v1/a2a", tags=["a2a"])
logger = logging.getLogger(__name__)


def get_a2a_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> A2aService:
    transport = A2aClientTransport(
        public_base_url=settings.a2a_public_base_url,
        timeout_seconds=settings.a2a_timeout_seconds,
    )
    return A2aService(transport=transport, settings=settings)


@router.get("/agents", response_model=ApiResponse)
async def list_a2a_agents(
    service: Annotated[A2aService, Depends(get_a2a_service)],
) -> ApiResponse:
    agents = service.list_agents()
    return ApiResponse(data={"agents": [agent.model_dump() for agent in agents]})


@router.get("/agents/{agent_name}/card", response_model=ApiResponse)
async def get_a2a_agent_card(
    agent_name: str,
    service: Annotated[A2aService, Depends(get_a2a_service)],
) -> ApiResponse:
    try:
        card = await service.get_agent_card(agent_name)
        return ApiResponse(data={"agent_name": agent_name, "card": card})
    except ValueError as exc:
        raise_bad_request(exc)
    except Exception as exc:
        logger.exception("a2a agent card fetch failed", extra={"agent_name": agent_name})
        raise_internal_server_error(exc, detail="Failed to fetch A2A agent card")


@router.post("/demo/message", response_model=ApiResponse)
async def send_a2a_message(
    payload: A2aMessageRequest,
    service: Annotated[A2aService, Depends(get_a2a_service)],
) -> ApiResponse:
    try:
        result = await service.send_message(
            agent_name=payload.agent_name,
            input_text=payload.input_text,
        )
        return ApiResponse(data=result.model_dump())
    except ValueError as exc:
        raise_bad_request(exc)
    except Exception as exc:
        logger.exception(
            "a2a message send failed",
            extra={"agent_name": payload.agent_name},
        )
        raise_internal_server_error(exc, detail="Failed to send A2A message")


@router.post("/demo/full-flow", response_model=ApiResponse)
async def run_a2a_full_flow(
    payload: A2aFullFlowRequest,
    service: Annotated[A2aService, Depends(get_a2a_service)],
) -> ApiResponse:
    try:
        result = await service.run_full_flow(
            agent_names=payload.agent_names,
            use_sample_messages=payload.use_sample_messages,
            input_text=payload.input_text,
        )
        return ApiResponse(data=result.model_dump())
    except ValueError as exc:
        raise_bad_request(exc)
    except Exception as exc:
        logger.exception("a2a full-flow test failed")
        raise_internal_server_error(exc, detail="Failed to run A2A full-flow test")
