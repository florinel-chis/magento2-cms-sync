"""
Fake Magento 2 REST API for tests and local development.

Only the endpoints this project uses are implemented:

    GET  /rest/V1/store/storeViews
    GET  /rest/V1/cmsBlock/search          GET  /rest/V1/cmsPage/search
    GET  /rest/V1/cmsBlock/{id}            GET  /rest/V1/cmsPage/{id}
    POST /rest/V1/cmsBlock                 POST /rest/V1/cmsPage
    PUT  /rest/V1/cmsBlock/{id}            PUT  /rest/V1/cmsPage/{id}

Usage in tests::

    magento = FakeMagento(tokens=["secret"])
    magento.seed_stock_pages()
    app = create_app(magento)            # ASGI app, drive it with httpx.ASGITransport

Usage as a standalone server (two of these make a source/destination pair)::

    python -m tests.magento_stub --port 8081 --token secret --seed demo
    python -m tests.magento_stub --port 8082 --token secret --seed demo-dest
"""
from .app import (
    BLOCK_FIELDS,
    PAGE_FIELDS,
    FakeMagento,
    MagentoError,
    RecordedRequest,
    create_app,
)
from .transport import StubNetwork, patch_magento_client

__all__ = [
    "BLOCK_FIELDS",
    "PAGE_FIELDS",
    "FakeMagento",
    "MagentoError",
    "RecordedRequest",
    "StubNetwork",
    "create_app",
    "patch_magento_client",
]
