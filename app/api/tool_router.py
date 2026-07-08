import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.error_utils import raise_bad_request, raise_internal_server_error
from app.schemas.common import ApiResponse
from app.schemas.tool import ToolExecuteRequest
from app.service.tool_service import ToolService

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])
logger = logging.getLogger(__name__)


def get_tool_service() -> ToolService:
    return ToolService()


@router.get("", response_model=ApiResponse)
async def list_tools(
    service: Annotated[ToolService, Depends(get_tool_service)],
) -> ApiResponse:
    return ApiResponse(data={"tools": service.list_tools()})


@router.post("", response_model=ApiResponse)
async def execute_tool(
    payload: ToolExecuteRequest,
    service: Annotated[ToolService, Depends(get_tool_service)],
) -> ApiResponse:
    try:
        result = await service.execute(
            tool_name=payload.tool_name,
            arguments=payload.arguments,
        )
        return ApiResponse(data={"tool_name": payload.tool_name, "result": result})
    except ValueError as exc:
        raise_bad_request(exc)
    except Exception as exc:
        logger.exception("tool execution failed", extra={"tool_name": payload.tool_name})
        raise_internal_server_error(exc, detail="Failed to execute tool")
