"""Process-wide in-memory checkpointer for LangGraph demo endpoints (dev / demo only)."""

from langgraph.checkpoint.memory import InMemorySaver

_demo_saver: InMemorySaver | None = None


def get_demo_in_memory_saver() -> InMemorySaver:
    """Return a shared saver so multi-turn demos persist by ``thread_id`` within the process."""
    global _demo_saver
    if _demo_saver is None:
        _demo_saver = InMemorySaver()
    return _demo_saver
