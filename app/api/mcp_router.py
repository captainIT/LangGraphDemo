import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.schemas.common import ApiResponse
from app.schemas.mcp import (
    McpFullFlowRequest,
    McpServerFlowRequest,
    McpToolInvokeRequest,
)
from app.service.mcp_service import McpService
from app.transport.mcp_client import McpClientTransport

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])
logger = logging.getLogger(__name__)


def get_mcp_service(settings: Annotated[Settings, Depends(get_settings)]) -> McpService:
    transport = McpClientTransport(
        tool_name_prefix=settings.mcp_tool_name_prefix,
        timeout_seconds=settings.mcp_timeout_seconds,
    )
    return McpService(transport=transport)


@router.get("/servers", response_model=ApiResponse)
async def list_mcp_servers(
    service: Annotated[McpService, Depends(get_mcp_service)],
) -> ApiResponse:
    servers = service.list_servers()
    return ApiResponse(data={"servers": [server.model_dump() for server in servers]})


@router.get("/tools", response_model=ApiResponse)
async def list_mcp_tools(
    service: Annotated[McpService, Depends(get_mcp_service)],
) -> ApiResponse:
    try:
        tools = await service.list_tools()
        return ApiResponse(data={"tools": [tool.model_dump() for tool in tools]})
    except Exception as exc:
        logger.exception("mcp tool discovery failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list MCP tools",
        ) from exc


@router.post("/tools/invoke", response_model=ApiResponse)
async def invoke_mcp_tool(
    payload: McpToolInvokeRequest,
    service: Annotated[McpService, Depends(get_mcp_service)],
) -> ApiResponse:
    try:
        result = await service.invoke_tool(
            tool_name=payload.tool_name,
            arguments=payload.arguments,
            server_name=payload.server_name,
        )
        return ApiResponse(data=result.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("mcp tool invocation failed", extra={"tool_name": payload.tool_name})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invoke MCP tool",
        ) from exc


@router.post("/demo/full-flow", response_model=ApiResponse)
async def run_mcp_full_flow(
    payload: McpFullFlowRequest,
    service: Annotated[McpService, Depends(get_mcp_service)],
) -> ApiResponse:
    try:
        result = await service.run_full_flow(
            server_names=payload.server_names,
            include_tool_invocations=payload.include_tool_invocations,
        )
        return ApiResponse(data=result.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("mcp full-flow test failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run MCP full-flow test",
        ) from exc


@router.post("/demo/server/{server_name}", response_model=ApiResponse)
async def run_mcp_server_flow(
    server_name: str,
    payload: McpServerFlowRequest,
    service: Annotated[McpService, Depends(get_mcp_service)],
) -> ApiResponse:
    try:
        result = await service.run_server_flow(
            server_name=server_name,
            include_tool_invocations=payload.include_tool_invocations,
        )
        return ApiResponse(data=result.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("mcp server flow test failed", extra={"server_name": server_name})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run MCP server flow test",
        ) from exc
