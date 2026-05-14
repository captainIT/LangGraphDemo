"""LangGraph demo: prebuilt ReAct agent (``create_react_agent``)."""

import warnings

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.warnings import LangGraphDeprecatedSinceV10


def build_react_demo_graph(llm: BaseChatModel, tools: list[BaseTool]):
    """Return a compiled ReAct-style tool loop (LangGraph prebuilt)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=LangGraphDeprecatedSinceV10)
        return create_react_agent(llm, tools)
