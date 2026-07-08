"""A2A client transport wrapper."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
from google.protobuf.json_format import ParseDict

from a2a.client import ClientConfig, ClientFactory
from a2a.client.client import Client
from a2a.helpers.proto_helpers import get_stream_response_text
from a2a.server.request_handlers.response_helpers import agent_card_to_dict
from a2a.types.a2a_pb2 import AgentCard, Role, SendMessageRequest
from a2a.helpers.proto_helpers import new_text_message
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH


class A2aClientTransport:
    def __init__(
        self,
        public_base_url: str,
        timeout_seconds: float,
    ) -> None:
        self._public_base_url = public_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def agent_base_url(self, agent_path: str) -> str:
        return f"{self._public_base_url}{agent_path.rstrip('/')}/"

    async def fetch_agent_card(self, agent_path: str) -> AgentCard:
        base_url = self.agent_base_url(agent_path)
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(f"{base_url.rstrip('/')}{AGENT_CARD_WELL_KNOWN_PATH}")
            response.raise_for_status()
            return ParseDict(response.json(), AgentCard(), ignore_unknown_fields=True)

    async def fetch_agent_card_dict(self, agent_path: str) -> dict:
        card = await self.fetch_agent_card(agent_path)
        return agent_card_to_dict(card)

    def create_client(self, agent_card: AgentCard) -> Client:
        httpx_client = httpx.AsyncClient(timeout=self._timeout_seconds)
        factory = ClientFactory(ClientConfig(httpx_client=httpx_client))
        return factory.create(agent_card)

    async def send_text_message(
        self,
        agent_path: str,
        input_text: str,
    ) -> tuple[list[str], AgentCard]:
        card = await self.fetch_agent_card(agent_path)
        client = self.create_client(card)

        request = SendMessageRequest()
        request.message.CopyFrom(new_text_message(input_text, role=Role.ROLE_USER))

        chunks: list[str] = []
        async for stream_response in client.send_message(request):
            text = get_stream_response_text(stream_response)
            if text:
                chunks.append(text)

        await client.close()
        return chunks, card

    async def stream_text_message(
        self,
        agent_path: str,
        input_text: str,
    ) -> AsyncIterator[str]:
        card = await self.fetch_agent_card(agent_path)
        client = self.create_client(card)

        request = SendMessageRequest()
        request.message.CopyFrom(new_text_message(input_text, role=Role.ROLE_USER))

        try:
            async for stream_response in client.send_message(request):
                text = get_stream_response_text(stream_response)
                if text:
                    yield text
        finally:
            await client.close()
