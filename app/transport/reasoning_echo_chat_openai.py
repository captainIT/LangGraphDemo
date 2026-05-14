"""ChatOpenAI subclass for OpenAI-compatible APIs that require reasoning round-trips."""

from typing import Any

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI


class ReasoningEchoChatOpenAI(ChatOpenAI):
    """Preserve ``reasoning_content`` / ``reasoning_details`` across tool-calling turns.

    The default ChatOpenAI chat-completions path drops provider-specific assistant fields
    when building ``AIMessage`` and when serializing history. Some compatible endpoints
    (thinking / reasoning mode) reject the follow-up request unless those fields are
    echoed back unchanged.
    """

    def _create_chat_result(
        self,
        response: dict[str, Any] | Any,
        generation_info: dict[str, Any] | None = None,
    ) -> ChatResult:
        result = super()._create_chat_result(response, generation_info=generation_info)
        choices: list[Any]
        if isinstance(response, dict):
            choices = list(response.get("choices") or [])
        else:
            raw_choices = getattr(response, "choices", None)
            choices = list(raw_choices) if raw_choices is not None else []

        for idx, choice in enumerate(choices):
            if idx >= len(result.generations):
                break
            ai_msg = result.generations[idx].message
            if not isinstance(ai_msg, AIMessage):
                continue
            raw_msg: dict[str, Any]
            if isinstance(choice, dict):
                raw_msg = dict(choice.get("message") or {})
            else:
                msg_obj = getattr(choice, "message", None)
                if msg_obj is None:
                    continue
                raw_msg = (
                    msg_obj.model_dump()
                    if hasattr(msg_obj, "model_dump")
                    else dict(msg_obj)
                )
            for key in ("reasoning_content", "reasoning_details"):
                val = raw_msg.get(key)
                if val is not None:
                    ai_msg.additional_kwargs[key] = val
        return result

    def _get_request_payload(
        self,
        input_: LanguageModelInput,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        api_messages = payload.get("messages")
        if not isinstance(api_messages, list):
            return payload
        messages = self._convert_input(input_).to_messages()
        if len(api_messages) != len(messages):
            return payload
        for api_dict, lc_msg in zip(api_messages, messages, strict=True):
            if not isinstance(lc_msg, AIMessage) or not isinstance(api_dict, dict):
                continue
            for key in ("reasoning_content", "reasoning_details"):
                val = lc_msg.additional_kwargs.get(key)
                if val is not None:
                    api_dict[key] = val
        return payload
