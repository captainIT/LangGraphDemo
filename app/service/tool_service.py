from typing import Any

from langchain_core.tools import BaseTool

from app.utils.tool_functions import (
    add_numbers,
    count_words,
    get_current_utc_time,
    slugify_text,
)


class ToolService:
    def __init__(self) -> None:
        self._tool_map: dict[str, BaseTool] = {
            get_current_utc_time.name: get_current_utc_time,
            add_numbers.name: add_numbers,
            count_words.name: count_words,
            slugify_text.name: slugify_text,
        }

    def list_tools(self) -> list[str]:
        return sorted(self._tool_map.keys())

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        selected = self._tool_map.get(tool_name)
        if not selected:
            raise ValueError(f"Unsupported tool: {tool_name}")
        return await selected.ainvoke(arguments)
