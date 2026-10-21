"""Contract tests for the fake Magento itself: it must behave like Magento 2.4 REST."""
import httpx
import pytest

from tests.conftest import TOKEN
from tests.magento_stub import BLOCK_FIELDS, PAGE_FIELDS, FakeMagento, create_app


async def test_requires_bearer_token(magento):
    transport = httpx.ASGITransport(app=create_app(magento))
    async with httpx.AsyncClient(transport=transport, base_url="http://magento.test") as anon:
        r = await anon.get("/rest/V1/cmsBlock/search", params={"searchCriteria[pageSize]": 10})
        assert r.status_code == 401
        assert r.json() == {"message": "The consumer isn't authorized to access %resources.",
                            "parameters": {"resources": "Magento_Cms::block"}}
        r = await anon.get("/rest/V1/cmsBlock/1", headers={"Authorization": "Bearer wrong"})
        assert r.status_code == 401


async def test_search_requires_search_criteria(magento_http):
    r = await magento_http.get("/rest/V1/cmsBlock/search")
    assert r.status_code == 400
    assert r.json() == {"message": "%fieldName is a required field.", "parameters": {"fieldName": "searchCriteria"}}


async def test_block_output_matches_core_interface(magento_http, magento):
    r = await magento_http.get("/rest/V1/cmsBlock/search", params={"searchCriteria[pageSize]": 100})
    body = r.json()
    assert set(body) == {"items", "search_criteria", "total_count"}
    assert body["total_count"] == 3
    item = body["items"][0]
    assert set(item) <= set(BLOCK_FIELDS)
    assert isinstance(item["id"], int) and isinstance(item["active"], bool)
    for forbidden in ("store_id", "is_active", "block_id", "url_key"):
        assert forbidden not in item
    assert body["items"][2]["active"] is False


async def test_page_output_matches_core_interface(magento_http):
    r = await magento_http.get("/rest/V1/cmsPage/search", params={"searchCriteria[pageSize]": 100})
    items = r.json()["items"]
    assert [p["identifier"] for p in items] == ["no-route", "home", "enable-cookies", "privacy-policy-cookie-restriction-mode"]
    home = next(p for p in items if p["identifier"] == "home")
    assert set(home) <= set(PAGE_FIELDS)
    assert home["sort_order"] == "0" and home["page_layout"] == "1column"
    # nullable fields that are NULL in the database are omitted, not emitted as null
    assert "custom_theme" not in home and "layout_update_xml" not in home


async def test_search_paginates_and_clamps_to_last_page(magento_http, magento):
    magento.seed_blocks(250)
    pages = []
    for current in (1, 2, 3):
        r = await magento_http.get("/rest/V1/cmsBlock/search", params={
            "searchCriteria[pageSize]": 100, "searchCriteria[currentPage]": current})
        body = r.json()
        assert body["total_count"] == 253
        assert body["search_criteria"]["page_size"] == 100
        pages.append(body["items"])
    assert [len(p) for p in pages] == [100, 100, 53]
    ids = [i["id"] for p in pages for i in p]
    assert ids == sorted(set(ids))
    # Magento's collection clamps currentPage to the last page instead of returning []
    r = await magento_http.get("/rest/V1/cmsBlock/search", params={
        "searchCriteria[pageSize]": 100, "searchCriteria[currentPage]": 99})
    assert r.json()["items"] == pages[2]
    # omitted pageSize returns everything
    r = await magento_http.get("/rest/V1/cmsBlock/search", params={"searchCriteria": ""})
    assert len(r.json()["items"]) == 253


async def test_search_filters(magento_http):
    r = await magento_http.get("/rest/V1/cmsBlock/search", params={
        "searchCriteria[filter_groups][0][filters][0][field]": "identifier",
        "searchCriteria[filter_groups][0][filters][0][value]": "contact-us-info"})
    assert [b["identifier"] for b in r.json()["items"]] == ["contact-us-info"]
    r = await magento_http.get("/rest/V1/cmsBlock/search", params={
        "searchCriteria[filter_groups][0][filters][0][field]": "identifier",
        "searchCriteria[filter_groups][0][filters][0][value]": "%_%",
        "searchCriteria[filter_groups][0][filters][0][condition_type]": "like",
        "searchCriteria[filter_groups][1][filters][0][field]": "active",
        "searchCriteria[filter_groups][1][filters][0][value]": "True"})
    assert [b["identifier"] for b in r.json()["items"]] == ["footer_links_block"]


async def test_get_missing_entity_is_404_with_magento_message(magento_http):
    r = await magento_http.get("/rest/V1/cmsBlock/999")
    assert r.status_code == 404
    assert r.json() == {"message": 'The CMS block with the "%1" ID doesn\'t exist.', "parameters": ["999"]}
    r = await magento_http.get("/rest/V1/cmsPage/999")
    assert r.json()["message"] == 'The CMS page with the "%1" ID doesn\'t exist.'


async def test_create_block_assigns_id_and_timestamps(magento_http, magento):
    r = await magento_http.post("/rest/V1/cmsBlock", json={"block": {
        "identifier": "new_block", "title": "New", "content": "<p>x</p>", "active": True}})
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["id"] == 4 and created["identifier"] == "new_block"
    assert created["creation_time"] == created["update_time"]
    assert magento.find_block("new_block")["content"] == "<p>x</p>"


async def test_create_rejects_unknown_property_like_magento(magento_http):
    r = await magento_http.post("/rest/V1/cmsBlock", json={"block": {
        "identifier": "x", "title": "x", "content": "", "block_id": 7}})
    assert r.status_code == 400
    assert r.json()["message"] == ('Property "BlockId" does not have accessor method "getBlockId" '
                                   'in class "Magento\\Cms\\Api\\Data\\BlockInterface".')
    r = await magento_http.post("/rest/V1/cmsPage", json={"page": {"identifier": "x", "title": "x", "store_id": [0]}})
    assert r.status_code == 400 and "StoreId" in r.json()["message"]


async def test_create_duplicate_identifier_is_rejected(magento_http):
    r = await magento_http.post("/rest/V1/cmsBlock", json={"block": {"identifier": "sale_coupon", "title": "dup"}})
    assert r.status_code == 400
    assert r.json()["message"] == "A block identifier with the same properties already exists in the selected store."
    r = await magento_http.post("/rest/V1/cmsPage", json={"page": {"identifier": "home", "title": "dup"}})
    assert r.status_code == 400 and "URL key" in r.json()["message"]


async def test_post_with_existing_id_overwrites_that_entity(magento_http, magento):
    """Magento saves the entity whose id is in the body, so a 'create' carrying a foreign
    id silently overwrites an unrelated destination block. The stub reproduces this."""
    victim = magento.find_block("contact-us-info")
    r = await magento_http.post("/rest/V1/cmsBlock", json={"block": {
        "id": victim["id"], "identifier": "imported_block", "title": "Imported", "content": "<p>imported</p>"}})
    assert r.status_code == 200
    assert magento.find_block("contact-us-info") is None
    assert magento.find_block("imported_block")["id"] == victim["id"]


async def test_post_with_unknown_id_fails(magento_http):
    r = await magento_http.post("/rest/V1/cmsBlock", json={"block": {"id": 4242, "identifier": "ghost", "title": "g"}})
    assert r.status_code == 400
    assert r.json()["message"].startswith("Could not save the block:")


async def test_put_uses_body_id_not_url_id(magento_http, magento):
    footer, contact = magento.find_block("footer_links_block"), magento.find_block("contact-us-info")
    r = await magento_http.put(f"/rest/V1/cmsBlock/{footer['id']}", json={"block": {
        "id": contact["id"], "identifier": "contact-us-info", "title": "Renamed via PUT", "content": "<p>c</p>"}})
    assert r.status_code == 200
    assert magento.find_block("contact-us-info")["title"] == "Renamed via PUT"
    assert magento.find_block("footer_links_block")["title"] == "Footer Links"


async def test_is_active_input_alias_and_time_fields_are_server_controlled(magento_http, magento):
    r = await magento_http.put("/rest/V1/cmsBlock/1", json={"block": {
        "id": 1, "identifier": "footer_links_block", "is_active": False,
        "creation_time": "1999-01-01 00:00:00", "update_time": "1999-01-01 00:00:00"}})
    assert r.status_code == 200
    body = r.json()
    assert body["active"] is False
    assert not body["creation_time"].startswith("1999")


async def test_store_views(magento_http):
    r = await magento_http.get("/rest/V1/store/storeViews")
    assert [s["code"] for s in r.json()] == ["admin", "default"]


async def test_fail_next_injects_errors_then_recovers(magento_http, magento):
    magento.fail_next(503, "Service Unavailable", times=2, method="GET", path="cmsBlock/search")
    for _ in range(2):
        r = await magento_http.get("/rest/V1/cmsBlock/search", params={"searchCriteria[pageSize]": 1})
        assert r.status_code == 503 and r.json() == {"message": "Service Unavailable"}
    r = await magento_http.get("/rest/V1/cmsBlock/search", params={"searchCriteria[pageSize]": 1})
    assert r.status_code == 200
    assert len(magento.requests_for("GET", "cmsBlock/search")) == 3


async def test_store_code_prefixes_and_unknown_routes(magento_http):
    for prefix in ("/rest/V1", "/rest/all/V1", "/rest/default/V1"):
        r = await magento_http.get(f"{prefix}/cmsBlock/1")
        assert r.status_code == 200
    r = await magento_http.get("/rest/V1/products")
    assert r.status_code == 404 and r.json()["message"] == "Request does not match any route."


async def test_emit_store_id_mode_for_extended_installs():
    m = FakeMagento(tokens=[TOKEN], emit_store_id=True)
    m.add_block("b", store_id=[1, 2])
    transport = httpx.ASGITransport(app=create_app(m))
    async with httpx.AsyncClient(transport=transport, base_url="http://m.test",
                                 headers={"Authorization": f"Bearer {TOKEN}"}) as c:
        r = await c.get("/rest/V1/cmsBlock/1")
        assert r.json()["store_id"] == [1, 2]
        r = await c.post("/rest/V1/cmsBlock", json={"block": {"identifier": "c", "title": "c", "store_id": [1]}})
        assert r.status_code == 200 and r.json()["store_id"] == [1]
