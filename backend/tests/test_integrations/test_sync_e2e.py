"""End-to-end: the real FastAPI app syncing between two fake Magento instances."""
import pytest

from tests.conftest import DEST_HOST, SOURCE_HOST, TOKEN

pytestmark = pytest.mark.integration


async def _create_instances(api):
    src = await api.post("/api/instances/", json={"name": "Source", "url": f"http://{SOURCE_HOST}", "api_token": TOKEN})
    dst = await api.post("/api/instances/", json={"name": "Destination", "url": f"http://{DEST_HOST}", "api_token": TOKEN})
    assert src.status_code == 200 and dst.status_code == 200, (src.text, dst.text)
    return src.json()["id"], dst.json()["id"]


async def test_connection_test(api, dest_magento):
    src_id, dst_id = await _create_instances(api)
    r = await api.post(f"/api/instances/{src_id}/test")
    assert r.json()["success"] is True
    assert [s["code"] for s in r.json()["store_views"]] == ["admin", "default"]

    dest_magento.tokens = {"rotated"}
    r = await api.post(f"/api/instances/{dst_id}/test")
    assert r.json() == {"success": False, "message": "Authentication failed. Please check your API token.",
                        "version": None, "store_views": None}


async def test_compare_blocks_reports_drift(api):
    src_id, dst_id = await _create_instances(api)
    r = await api.post("/api/compare/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["total_source"], body["total_destination"]) == (3, 2)
    assert (body["exists_in_both"], body["missing_in_destination"], body["missing_in_source"], body["different"]) == (1, 2, 1, 1)
    by_id = {i["identifier"]: i for i in body["items"]}
    assert by_id["footer_links_block"]["differences"] == ["content"]
    assert by_id["dest_only_block"]["source_status"] == "missing"

    snap = await api.get(f"/api/instances/{src_id}/data-snapshots")
    assert snap.json()["blocks"]["count"] == 3 and snap.json()["pages"] is None


async def test_full_block_sync_flow(api, source_magento, dest_magento):
    src_id, dst_id = await _create_instances(api)
    r = await api.post("/api/compare/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})
    assert r.status_code == 200

    items = [{"identifier": "contact-us-info", "action": "create"},
             {"identifier": "sale_coupon", "action": "create"},
             {"identifier": "footer_links_block", "action": "update"}]
    preview = await api.post("/api/sync/preview", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "data_type": "blocks", "items": items})
    assert preview.status_code == 200
    assert (preview.json()["creates"], preview.json()["updates"]) == (2, 1)

    started = await api.post("/api/sync/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "data_type": "blocks", "items": items})
    assert started.status_code == 200, started.text
    sync_id = started.json()["sync_id"]

    # BackgroundTasks run inside the ASGI call, so the sync is finished once we get here.
    status = (await api.get(f"/api/sync/status/{sync_id}")).json()
    assert status["status"] == "completed", status
    assert (status["items_synced"], status["items_failed"]) == (3, 0), status["details"]

    dest_footer = dest_magento.find_block("footer_links_block")
    assert dest_footer["content"] == source_magento.find_block("footer_links_block")["content"]
    assert dest_footer["id"] == 1, "update must keep the destination id"
    assert dest_magento.find_block("contact-us-info")["content"] == "<p>Call us: +40 000 000 000</p>"
    assert dest_magento.find_block("sale_coupon") is not None
    assert dest_magento.find_block("dest_only_block") is not None, "unrelated destination block must survive"
    assert len(dest_magento.blocks) == 4

    posted = [r.body["block"] for r in dest_magento.requests_for("POST", "/cmsBlock")]
    assert posted and all("id" not in b and "creation_time" not in b for b in posted)

    again = (await api.post("/api/compare/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})).json()
    assert (again["different"], again["missing_in_destination"]) == (0, 0), [
        (i["identifier"], i["differences"]) for i in again["items"] if i["differences"]]


async def test_full_page_sync_flow(api, source_magento, dest_magento):
    src_id, dst_id = await _create_instances(api)
    source_magento.pages[2]["content"] = "<p>New homepage</p>"  # drift the source 'home' page
    r = await api.post("/api/compare/pages", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})
    body = r.json()
    assert (body["total_source"], body["total_destination"], body["different"], body["missing_in_destination"]) == (5, 4, 1, 1)

    items = [{"identifier": "about-us", "action": "create"},
             {"identifier": "home", "action": "update", "fields_to_sync": ["content"]}]
    started = await api.post("/api/sync/pages", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "data_type": "pages", "items": items})
    status = (await api.get(f"/api/sync/status/{started.json()['sync_id']}")).json()
    assert status["status"] == "completed" and status["items_failed"] == 0, status

    assert dest_magento.find_page("home")["content"] == "<p>New homepage</p>"
    assert dest_magento.find_page("home")["title"] == "Home page"
    assert dest_magento.find_page("about-us")["content_heading"] == "About us"

    diff = await api.post("/api/compare/diff", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "data_type": "pages", "identifier": "home"})
    assert all(not f["is_different"] for f in diff.json()["fields"])


async def test_sync_records_per_item_failures(api, dest_magento):
    src_id, dst_id = await _create_instances(api)
    await api.post("/api/compare/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})
    dest_magento.fail_next(400, "A block identifier with the same properties already exists in the selected store.",
                           method="POST", path="/cmsBlock$")
    items = [{"identifier": "contact-us-info", "action": "create"},
             {"identifier": "sale_coupon", "action": "create"},
             {"identifier": "does-not-exist", "action": "create"}]
    started = await api.post("/api/sync/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "data_type": "blocks", "items": items})
    status = (await api.get(f"/api/sync/status/{started.json()['sync_id']}")).json()
    assert status["status"] == "completed"
    assert (status["items_synced"], status["items_failed"]) == (1, 2)
    errors = {d["identifier"]: d["error"] for d in status["details"] if not d["success"]}
    assert "400" in errors["contact-us-info"]
    assert errors["does-not-exist"] == "Source item not found: does-not-exist"


async def test_update_without_destination_id_is_reported_not_crashed(api, dest_magento):
    """Snapshots from an install whose API omits 'id' must yield a clear per-item error."""
    from config import settings
    import json
    src_id, dst_id = await _create_instances(api)
    await api.post("/api/compare/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})
    snapshot = settings.instances_data_dir / str(dst_id) / "blocks.json"
    stripped = [{k: v for k, v in b.items() if k != "id"} for b in json.loads(snapshot.read_text())]
    snapshot.write_text(json.dumps(stripped))
    # execute_sync re-reads the destination live, so make the live stub omit ids too
    dest_magento._public = lambda e, kind, _orig=dest_magento._public: {  # type: ignore[method-assign]
        k: v for k, v in _orig(e, kind).items() if k != "id"}

    started = await api.post("/api/sync/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "data_type": "blocks",
        "items": [{"identifier": "footer_links_block", "action": "update"}]})
    status = (await api.get(f"/api/sync/status/{started.json()['sync_id']}")).json()
    assert status["status"] == "completed" and status["items_failed"] == 1
    assert status["details"][0]["error"] == "Destination item has no id: footer_links_block"
    assert dest_magento.find_block("footer_links_block")["content"] == '<ul><li><a href="/about">About</a></li></ul>'
    assert not dest_magento.requests_for("PUT")


async def test_sync_marks_history_failed_when_destination_is_down(api, dest_magento):
    src_id, dst_id = await _create_instances(api)
    await api.post("/api/compare/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})
    dest_magento.tokens = set()  # every call to the destination is now 401
    started = await api.post("/api/sync/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "data_type": "blocks",
        "items": [{"identifier": "sale_coupon", "action": "create"}]})
    status = (await api.get(f"/api/sync/status/{started.json()['sync_id']}")).json()
    assert status["status"] == "failed"
    assert "401" in status["error_message"]


async def test_comparison_ignores_server_timestamps_and_detects_active_flag(api, source_magento, dest_magento):
    """Timestamps differ on every real Magento pair; the active flag is spelled 'active' by Magento."""
    src_id, dst_id = await _create_instances(api)
    dest_magento.clock = lambda: "2031-01-01 00:00:00"
    dest_magento.blocks[1]["content"] = source_magento.blocks[1]["content"]   # same content, other clock
    dest_magento.blocks[1]["update_time"] = "2031-01-01 00:00:00"
    source_magento.blocks[1]["active"] = False                              # but a real difference
    body = (await api.post("/api/compare/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})).json()
    footer = next(i for i in body["items"] if i["identifier"] == "footer_links_block")
    assert footer["differences"] == ["active"]
    diff = (await api.post("/api/compare/diff", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "data_type": "blocks",
        "identifier": "footer_links_block"})).json()
    assert {f["field_name"] for f in diff["fields"]} == {"title", "content", "active", "sort_order"}


async def test_api_never_returns_the_token_and_keeps_it_when_omitted_on_update(api, source_magento):
    created = (await api.post("/api/instances/", json={
        "name": "Source", "url": f"http://{SOURCE_HOST}", "api_token": TOKEN})).json()
    assert "api_token" not in created
    listed = (await api.get("/api/instances/")).json()
    assert all("api_token" not in i for i in listed)
    fetched = (await api.get(f"/api/instances/{created['id']}")).json()
    assert "api_token" not in fetched

    renamed = await api.put(f"/api/instances/{created['id']}", json={"name": "Source renamed"})
    assert renamed.status_code == 200 and "api_token" not in renamed.json()
    # the stored token still works, so it was kept
    assert (await api.post(f"/api/instances/{created['id']}/test")).json()["success"] is True

    comparison = (await api.post("/api/compare/blocks", json={
        "source_instance_id": created["id"], "destination_instance_id": created["id"], "force_refresh": True})).json()
    assert "api_token" not in comparison["source_instance"]


async def test_deleting_an_instance_removes_history_on_both_sides(api):
    src_id, dst_id = await _create_instances(api)
    await api.post("/api/compare/blocks", json={
        "source_instance_id": src_id, "destination_instance_id": dst_id, "force_refresh": True})
    for s, d in ((src_id, dst_id), (dst_id, src_id)):
        r = await api.post("/api/sync/blocks", json={
            "source_instance_id": s, "destination_instance_id": d, "data_type": "blocks",
            "items": [{"identifier": "footer_links_block", "action": "update"}]})
        assert r.status_code == 200
    assert (await api.get("/api/history/")).json()["total"] == 2

    assert (await api.delete(f"/api/instances/{dst_id}")).status_code == 200
    assert (await api.get("/api/history/")).json()["total"] == 0
    assert (await api.get(f"/api/instances/{dst_id}")).status_code == 404


async def test_startup_marks_abandoned_syncs_failed(api):
    from api.sync import fail_abandoned_syncs, ABANDONED_MESSAGE
    from models.database import AsyncSessionLocal
    from models.models import SyncHistory
    src_id, dst_id = await _create_instances(api)
    async with AsyncSessionLocal() as db:
        db.add(SyncHistory(source_instance_id=src_id, destination_instance_id=dst_id, sync_type="pages",
                           sync_status="in_progress", sync_details={}))
        db.add(SyncHistory(source_instance_id=src_id, destination_instance_id=dst_id, sync_type="blocks",
                           sync_status="pending", sync_details={}))
        db.add(SyncHistory(source_instance_id=src_id, destination_instance_id=dst_id, sync_type="blocks",
                           sync_status="completed", items_synced=1, sync_details={}))
        await db.commit()
        assert await fail_abandoned_syncs(db) == 2

    rows = (await api.get("/api/history/")).json()["items"]
    statuses = sorted((r["sync_type"], r["sync_status"]) for r in rows)
    assert statuses == [("blocks", "completed"), ("blocks", "failed"), ("pages", "failed")]
    failed = [r for r in rows if r["sync_status"] == "failed"]
    assert all(r["error_message"] == ABANDONED_MESSAGE and r["completed_at"] for r in failed)
