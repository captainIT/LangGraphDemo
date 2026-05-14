from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.agent_router import router as agent_router
from app.api.tool_router import router as tool_router
from app.config import get_settings
from app.schemas.common import ApiResponse
from app.utils.logger import setup_logging

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(agent_router)
app.include_router(tool_router)

_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_static_dir), html=True), name="ui")


@app.get("/health", response_model=ApiResponse)
async def health() -> ApiResponse:
    return ApiResponse(data={"status": "healthy"})
