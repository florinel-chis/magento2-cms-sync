"""
Route the project's outbound Magento HTTP calls into in-process stubs.

``integrations.magento_client.transport_override`` is the injection point: when set, every
``MagentoClient`` request goes through that httpx transport. ``StubNetwork`` is such a
transport, dispatching by hostname to one ``FakeMagento`` app each.
"""
from __future__ import annotations

from typing import Dict

import pytest

import httpx
from fastapi import FastAPI

from .app import FakeMagento, create_app


class StubNetwork(httpx.AsyncBaseTransport):
    """Dispatch requests to a stub app by hostname, e.g. ``source.magento.test``."""

    def __init__(self) -> None:
        self._hosts: Dict[str, httpx.ASGITransport] = {}

    def register(self, host: str, magento: FakeMagento) -> FastAPI:
        app = create_app(magento)
        self._hosts[host] = httpx.ASGITransport(app=app)
        return app

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        transport = self._hosts.get(request.url.host)
        if transport is None:
            raise httpx.ConnectError(f"no Magento stub registered for host {request.url.host!r}", request=request)
        return await transport.handle_async_request(request)

    async def aclose(self) -> None:
        for transport in self._hosts.values():
            await transport.aclose()


def patch_magento_client(monkeypatch: pytest.MonkeyPatch, network: StubNetwork) -> None:
    """Make ``integrations.magento_client`` talk to ``network`` instead of the internet."""
    import integrations.magento_client as client_module

    monkeypatch.setattr(client_module, "transport_override", network)
