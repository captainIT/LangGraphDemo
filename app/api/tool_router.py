import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.common import ApiResponse
from app.schemas.tool import ToolExecuteRequest
from app.service.tool_service import ToolService

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])
logger = logging.getLogger(__name__)
tool_service = ToolService()


@router.get("", response_model=ApiResponse)
async def list_tools() -> ApiResponse:
    return ApiResponse(data={"tools": tool_service.list_tools()})


@router.post("", response_model=ApiResponse)
async def execute_tool(payload: ToolExecuteRequest) -> ApiResponse:
    try:
        result = await tool_service.execute(
            tool_name=payload.tool_name,
            arguments=payload.arguments,
        )
        return ApiResponse(data={"tool_name": payload.tool_name, "result": result})
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("tool execution failed", extra={"tool_name": payload.tool_name})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute tool",
        ) from exc
