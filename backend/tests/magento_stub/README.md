# Fake Magento REST API

An in-memory stand-in for the parts of the Magento 2 REST API this project talks to.
It lets the backend be tested, and the UI be tried out, without installing Magento.

Shapes follow Magento 2.4 (`Magento\Cms\Api\Data\BlockInterface`, `PageInterface`,
`Magento\Store\Api\Data\StoreInterface`) and the
[Adobe Commerce REST reference](https://developer.adobe.com/commerce/webapi/rest/).

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/rest/V1/store/storeViews` | admin + default store views |
| GET | `/rest/V1/cmsBlock/search`, `/rest/V1/cmsPage/search` | `searchCriteria` required; `pageSize`, `currentPage`, `filter_groups` (eq, neq, like, in, nin, null, notnull) |
| GET | `/rest/V1/cmsBlock/{id}`, `/rest/V1/cmsPage/{id}` | 404 with Magento's message when missing |
| POST | `/rest/V1/cmsBlock`, `/rest/V1/cmsPage` | body wrapped in `block` / `page` |
| PUT | `/rest/V1/cmsBlock/{id}`, `/rest/V1/cmsPage/{id}` | the URL id is ignored, like Magento |

`/rest/all/V1/...` and `/rest/default/V1/...` work too. Everything needs
`Authorization: Bearer <token>`; anything else is a Magento-style 401.

## Magento behaviours reproduced on purpose

- Output uses interface getter names: `active`, never `is_active`. `store_id`, `url_key`,
  `block_id` and `page_id` are not in the core interfaces and are never returned.
  `FakeMagento(emit_store_id=True)` opts in to `store_id` for extended installs.
- Nullable fields that are NULL (for example `custom_theme` on stock pages) are omitted.
- Unknown input properties are rejected with 400
  (`Property "X" does not have accessor method "getX" ...`).
- A POST whose body contains `id` saves that entity: an existing id is overwritten,
  identifier included; an unknown id fails with 400.
- Duplicate identifiers in overlapping stores are rejected with Magento's messages.
- `currentPage` beyond the last page returns the last page again, as Magento's collection does.
- Omitting `pageSize` returns everything.

## In tests

```python
from tests.magento_stub import FakeMagento, StubNetwork, patch_magento_client

magento = FakeMagento(tokens=["secret"])
magento.seed_stock_pages()
magento.add_block("footer_links_block", "Footer Links", "<p>...</p>")

network = StubNetwork()
patch_magento_client(monkeypatch, network)        # MagentoClient now talks to stubs
network.register("source.magento.test", magento)  # reachable as http://source.magento.test

magento.fail_next(503, times=2)                   # fault injection for retry tests
magento.requests_for("POST", "/cmsBlock")         # every request is recorded
magento.find_block("footer_links_block")          # inspect state as Magento would return it
```

Shared fixtures live in `tests/conftest.py`: `magento`, `magento_http`, `network`,
`source_magento`, `dest_magento` and `api` (the real app on a throw-away database).

## As a local server

```bash
cd backend
python -m tests.magento_stub --port 8081 --token secret --seed demo        # "source"
python -m tests.magento_stub --port 8082 --token secret --seed demo-dest   # drifted "destination"
```

Add `http://127.0.0.1:8081` and `http://127.0.0.1:8082` as instances in the UI with token
`secret`, then compare and sync. `--blocks 500` generates extra blocks for pagination,
`--emit-store-id` and `--lenient` relax the stock-Magento strictness. State lives in memory
and resets on restart.
