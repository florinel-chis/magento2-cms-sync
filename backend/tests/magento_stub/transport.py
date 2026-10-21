"""
Route the project's outbound Magento HTTP calls into in-process stubs.

``MagentoClient`` builds its own ``httpx.AsyncClient`` per request, so there is no hook
to pass a transport. ``patch_magento_client`` swaps the ``httpx`` name inside the client
module for a thin namespace whose ``AsyncClient`` always carries a ``StubNetwork``
transport. Everything else (exception classes) is forwarded to the real httpx.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Dict

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


def patch_magento_client(monkeypatch, network: StubNetwork) -> None:
    """Make ``integrations.magento_client`` talk to ``network`` instead of the internet."""
    import integrations.magento_client as client_module

    def async_client(**kwargs):
        kwargs["transport"] = network
        return httpx.AsyncClient(**kwargs)

    shim = SimpleNamespace(
        AsyncClient=async_client,
        HTTPStatusError=httpx.HTTPStatusError,
        RequestError=httpx.RequestError,
        ConnectError=httpx.ConnectError,
        TimeoutException=httpx.TimeoutException,
    )
    monkeypatch.setattr(client_module, "httpx", shim)
