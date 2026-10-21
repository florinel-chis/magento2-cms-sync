"""The project's MagentoClient against the fake Magento."""
import httpx
import pytest

from integrations.magento_client import MagentoClient
from tests.conftest import SOURCE_HOST, TOKEN


@pytest.fixture
def client(source_magento) -> MagentoClient:
    return MagentoClient(base_url=f"http://{SOURCE_HOST}/", token=TOKEN)


async def test_get_store_views(client):
    views = await client.get_store_views()
    assert [v["code"] for v in views] == ["admin", "default"]


async def test_get_cms_blocks_collects_every_page(client, source_magento):
    source_magento.seed_blocks(250)
    blocks = await client.get_cms_blocks(page_size=100)
    assert len(blocks) == 253
    assert len({b["identifier"] for b in blocks}) == 253
    assert len(source_magento.requests_for("GET", "/cmsBlock/search")) == 3


async def test_get_cms_pages(client):
    pages = await client.get_cms_pages()
    assert {p["identifier"] for p in pages} == {
        "no-route", "home", "enable-cookies", "privacy-policy-cookie-restriction-mode", "about-us"}


async def test_wrong_token_raises_401(source_magento):
    bad = MagentoClient(base_url=f"http://{SOURCE_HOST}", token="nope")
    with pytest.raises(httpx.HTTPStatusError) as exc:
        await bad.get_store_views()
    assert exc.value.response.status_code == 401


async def test_unknown_host_raises_request_error(network):
    client = MagentoClient(base_url="http://nowhere.magento.test", token=TOKEN)
    with pytest.raises(httpx.RequestError):
        await client.get_store_views()


async def test_create_get_update_block_roundtrip(client, source_magento):
    created = await client.create_cms_block({"identifier": "roundtrip", "title": "RT", "content": "<p>1</p>", "active": True})
    fetched = await client.get_cms_block(created["id"])
    assert fetched == created
    updated = await client.update_cms_block(created["id"], {**fetched, "content": "<p>2</p>"})
    assert updated["content"] == "<p>2</p>"
    assert source_magento.find_block("roundtrip")["content"] == "<p>2</p>"


async def test_create_and_update_page_roundtrip(client, source_magento):
    created = await client.create_cms_page({"identifier": "faq", "title": "FAQ", "content": "<p>?</p>"})
    updated = await client.update_cms_page(created["id"], {"id": created["id"], "identifier": "faq", "title": "FAQ v2"})
    assert updated["title"] == "FAQ v2"
    assert source_magento.find_page("faq")["content"] == "<p>?</p>"


async def test_retries_5xx_then_succeeds(client, source_magento):
    source_magento.fail_next(502, "Bad Gateway", times=2)
    views = await client.get_store_views()
    assert len(views) == 2
    assert len(source_magento.requests_for("GET", "storeViews")) == 3


async def test_gives_up_after_retry_budget(client, source_magento):
    from config import settings
    source_magento.fail_next(500, times=settings.magento_retry_attempts + 1)
    with pytest.raises(httpx.HTTPStatusError) as exc:
        await client.get_store_views()
    assert exc.value.response.status_code == 500
    assert len(source_magento.requests_for("GET", "storeViews")) == settings.magento_retry_attempts + 1


async def test_does_not_retry_4xx(client, source_magento):
    source_magento.fail_next(400, "Bad Request", times=5)
    with pytest.raises(httpx.HTTPStatusError) as exc:
        await client.get_cms_block(1)
    assert exc.value.response.status_code == 400
    assert len(source_magento.requests_for("GET", "/cmsBlock/1")) == 1
