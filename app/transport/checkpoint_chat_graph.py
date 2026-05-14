"""LangGraph demo: message state + ``InMemorySaver`` checkpoint (multi-turn ``thread_id``)."""

from collections.abc import Sequence
from typing import Annotated

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class CheckpointChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def build_checkpoint_chat_graph(
    llm: BaseChatModel,
    checkpointer: BaseCheckpointSaver,
):
    async def chatbot(state: CheckpointChatState) -> dict[str, list[BaseMessage]]:
        raw = list(state["messages"])
        if not raw:
            return {"messages": []}
        if not isinstance(raw[0], SystemMessage):
            raw = [
                SystemMessage(
                    content="You are a helpful assistant. Keep answers short unless asked otherwise."
                ),
                *raw,
            ]
        response = await llm.ainvoke(raw)
        if not isinstance(response, AIMessage):
            return {"messages": [AIMessage(content=str(response.content))]}
        return {"messages": [response]}

    graph = StateGraph(CheckpointChatState)
    graph.add_node("chatbot", chatbot)
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    return graph.compile(checkpointer=checkpointer)
