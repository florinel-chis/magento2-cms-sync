"""
In-memory Magento 2 CMS REST fake.

Response and error shapes follow Magento 2.4 as defined by
``Magento\\Cms\\Api\\Data\\BlockInterface`` / ``PageInterface`` and the webapi error
format. Magento behaviours that regularly bite integrations are reproduced on purpose:

* Output keys come from the interface getters, so ``isActive()`` is emitted as
  ``active``. ``store_id``, ``url_key``, ``block_id`` and ``page_id`` are not part of the
  core interfaces and are never returned (``emit_store_id=True`` opts in to ``store_id``
  for installs that extend the API).
* Input properties without an interface accessor are rejected with HTTP 400, like
  Magento's ServiceInputProcessor does.
* A POST whose body carries an ``id`` saves THAT entity: Magento models update when an
  id is set. An existing id is overwritten (identifier included); an unknown id fails.
* PUT /cmsBlock/{id} ignores the URL id. The body ``id`` decides what gets saved, and a
  body without ``id`` creates a new entity.
* Search pagination clamps ``currentPage`` to the last page instead of returning an
  empty page, exactly like ``AbstractCollection::getCurPage()``.
"""
from __future__ import annotations

import copy
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Sequence

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

BLOCK_FIELDS: Sequence[str] = (
    "id", "identifier", "title", "content", "creation_time", "update_time", "active",
)
PAGE_FIELDS: Sequence[str] = (
    "id", "identifier", "title", "page_layout", "meta_title", "meta_keywords",
    "meta_description", "content_heading", "content", "creation_time", "update_time",
    "sort_order", "layout_update_xml", "custom_theme", "custom_root_template",
    "custom_layout_update_xml", "custom_theme_from", "custom_theme_to", "active",
)
# Keys Magento's input processor accepts: the interface properties, resolved through
# getters (``active`` -> ``isActive()``). ``is_active`` has no ``getIsActive``/``isIsActive``
# accessor and is rejected by stock Magento; the lenient mode accepts it as an alias.
_INPUT_KEYS = {
    "block": set(BLOCK_FIELDS),
    "page": set(PAGE_FIELDS),
}
# Search filters are applied to the database collection, so they use column names.
_FILTER_COLUMNS = {
    "block": {"block_id": "id", "is_active": "active", "store_id": "store_id", "identifier": "identifier",
              "title": "title", "content": "content", "creation_time": "creation_time", "update_time": "update_time"},
    "page": {"page_id": "id", "is_active": "active", "store_id": "store_id", **{f: f for f in PAGE_FIELDS
             if f not in ("id", "active")}},
}
_INTERFACE = {
    "block": "Magento\\Cms\\Api\\Data\\BlockInterface",
    "page": "Magento\\Cms\\Api\\Data\\PageInterface",
}
_PAGE_DEFAULTS: Dict[str, Any] = {
    "page_layout": "1column",
    "meta_title": "",
    "meta_keywords": "",
    "meta_description": "",
    "content_heading": "",
    "content": "",
    "sort_order": "0",
}
_BLOCK_DEFAULTS: Dict[str, Any] = {"content": ""}

# The four pages a fresh Magento 2.4 install ships with (Magento_Cms data patches).
STOCK_PAGES: List[Dict[str, Any]] = [
    {
        "identifier": "no-route",
        "title": "404 Not Found",
        "content_heading": "Whoops, our bad...",
        "content": (
            '<dl>\n<dt>The page you requested was not found, and we have a fine guess why.'
            "</dt>\n<dd>\n<ul class=\"disc\">\n<li>If you typed the URL directly, please make "
            "sure the spelling is correct.</li>\n<li>If you clicked on a link to get here, the "
            "link is outdated.</li>\n</ul></dd>\n</dl>"
        ),
        "page_layout": "2columns-right",
    },
    {
        "identifier": "home",
        "title": "Home page",
        "content_heading": "Home Page",
        "content": "<p>CMS homepage content goes here.</p>",
        "page_layout": "1column",
    },
    {
        "identifier": "enable-cookies",
        "title": "Enable Cookies",
        "content_heading": "What are Cookies?",
        "content": (
            '<div class="message info">\n<span>Please enable cookies in your web browser to '
            "continue.</span>\n</div>"
        ),
        "page_layout": "1column",
    },
    {
        "identifier": "privacy-policy-cookie-restriction-mode",
        "title": "Privacy and Cookie Policy",
        "content_heading": "Privacy and Cookie Policy",
        "content": "<p>This privacy policy sets out how this website uses and protects any information that you give us.</p>",
        "page_layout": "1column",
    },
]

STOCK_STORE_VIEWS: List[Dict[str, Any]] = [
    {"id": 0, "code": "admin", "name": "Admin", "website_id": 0, "store_group_id": 0, "is_active": 1},
    {"id": 1, "code": "default", "name": "Default Store View", "website_id": 1, "store_group_id": 1, "is_active": 1},
]

_FILTER_KEY = re.compile(
    r"^searchCriteria\[filter_groups\]\[(\d+)\]\[filters\]\[(\d+)\]\[(field|value|condition_type)\]$"
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _camel(snake: str) -> str:
    return "".join(part.capitalize() for part in snake.split("_"))


def _int(value: Any) -> int:
    """Coerce like Magento's input processor; anything else is its 400 'Invalid type' error."""
    try:
        return int(value)
    except (TypeError, ValueError):
        raise MagentoError(400, f'Invalid type for value: "{value}". Expected Type: "int".')


class MagentoError(Exception):
    """Raised inside handlers; rendered as Magento's ``{"message", "parameters"}`` body."""

    def __init__(self, status: int, message: str, parameters: Any = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.parameters = parameters

    def body(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"message": self.message}
        if self.parameters is not None:
            out["parameters"] = self.parameters
        return out


@dataclass
class RecordedRequest:
    method: str
    path: str
    params: Dict[str, str]
    body: Any = None


@dataclass
class _Fault:
    status: int
    message: str
    times: int
    method: Optional[str]
    path: Optional[re.Pattern]


@dataclass
class FakeMagento:
    """State container for one fake Magento instance."""

    name: str = "magento"
    tokens: Iterable[str] = ("test-token",)
    emit_store_id: bool = False
    strict_properties: bool = True
    clock: Callable[[], str] = _now  # creation_time/update_time source; freeze it for determinism
    blocks: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    pages: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    store_views: List[Dict[str, Any]] = field(default_factory=lambda: copy.deepcopy(STOCK_STORE_VIEWS))
    requests: List[RecordedRequest] = field(default_factory=list)
    _faults: List[_Fault] = field(default_factory=list, repr=False)
    _next_id: Dict[str, int] = field(default_factory=lambda: {"block": 1, "page": 1}, repr=False)

    def __post_init__(self) -> None:
        self.tokens = set(self.tokens)

    # ------------------------------------------------------------------ seeding
    def add_block(self, identifier: str, title: Optional[str] = None, content: str = "",
                  active: bool = True, store_id: Sequence[int] = (0,), **extra: Any) -> Dict[str, Any]:
        return self._add("block", identifier, title, content, active, store_id, extra)

    def add_page(self, identifier: str, title: Optional[str] = None, content: str = "",
                 active: bool = True, store_id: Sequence[int] = (0,), **extra: Any) -> Dict[str, Any]:
        return self._add("page", identifier, title, content, active, store_id, extra)

    def _add(self, kind: str, identifier: str, title: Optional[str], content: str, active: bool,
             store_id: Sequence[int], extra: Dict[str, Any]) -> Dict[str, Any]:
        return self._insert(kind, {"identifier": identifier, "title": title or identifier, "content": content,
                                   "active": active, "store_id": list(store_id), **extra})

    def seed_stock_pages(self) -> None:
        for page in STOCK_PAGES:
            self.add_page(**copy.deepcopy(page))

    def seed_blocks(self, count: int, prefix: str = "block") -> None:
        for n in range(1, count + 1):
            self.add_block(f"{prefix}-{n:04d}", title=f"Block {n}", content=f"<p>Content {n}</p>")

    def reset(self) -> None:
        self.blocks.clear()
        self.pages.clear()
        self.requests.clear()
        self._faults.clear()
        self._next_id = {"block": 1, "page": 1}

    # ------------------------------------------------------------------ inspection
    def find_block(self, identifier: str) -> Optional[Dict[str, Any]]:
        return next((self._public(b, "block") for b in self.blocks.values() if b["identifier"] == identifier), None)

    def find_page(self, identifier: str) -> Optional[Dict[str, Any]]:
        return next((self._public(p, "page") for p in self.pages.values() if p["identifier"] == identifier), None)

    def requests_for(self, method: Optional[str] = None, path_contains: Optional[str] = None) -> List[RecordedRequest]:
        return [r for r in self.requests
                if (method is None or r.method == method.upper())
                and (path_contains is None or path_contains in r.path)]

    # ------------------------------------------------------------------ fault injection
    def fail_next(self, status: int = 500,
                  message: str = "Internal Error. Details are available in Magento log file.",
                  times: int = 1, method: Optional[str] = None, path: Optional[str] = None) -> None:
        """Make the next ``times`` matching requests fail with ``status`` and ``message``."""
        self._faults.append(_Fault(status, message, times, method.upper() if method else None,
                                   re.compile(path) if path else None))

    def _take_fault(self, method: str, path: str) -> Optional[_Fault]:
        for fault in self._faults:
            if fault.method and fault.method != method:
                continue
            if fault.path and not fault.path.search(path):
                continue
            fault.times -= 1
            if fault.times <= 0:
                self._faults.remove(fault)
            return fault
        return None

    # ------------------------------------------------------------------ internals
    def _store(self, kind: str) -> Dict[int, Dict[str, Any]]:
        return self.blocks if kind == "block" else self.pages

    def _defaults(self, kind: str) -> Dict[str, Any]:
        return dict(_BLOCK_DEFAULTS if kind == "block" else _PAGE_DEFAULTS)

    def _insert(self, kind: str, data: Dict[str, Any]) -> Dict[str, Any]:
        store = self._store(kind)
        entity_id = data.pop("id", None) or self._next_id[kind]
        self._next_id[kind] = max(self._next_id[kind], entity_id + 1)
        now = self.clock()
        entity = {**self._defaults(kind), "id": entity_id, "creation_time": now, "update_time": now,
                  "active": True, "store_id": [0], **data}
        store[entity_id] = entity
        return self._public(entity, kind)

    def _public(self, entity: Dict[str, Any], kind: str) -> Dict[str, Any]:
        """Render an entity the way Magento's output processor does: interface getters only,
        null values omitted."""
        fields = BLOCK_FIELDS if kind == "block" else PAGE_FIELDS
        out = {k: entity[k] for k in fields if entity.get(k) is not None}
        if self.emit_store_id:
            out["store_id"] = list(entity.get("store_id") or [0])
        return out

    def _normalize_input(self, payload: Any, kind: str) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise MagentoError(400, "%fieldName is a required field.", {"fieldName": kind})
        allowed = set(_INPUT_KEYS[kind])
        if self.emit_store_id or not self.strict_properties:
            allowed.add("store_id")
        if not self.strict_properties:
            allowed.add("is_active")
        data: Dict[str, Any] = {}
        for key, value in payload.items():
            if key not in allowed:
                if self.strict_properties:
                    camel = _camel(key)
                    raise MagentoError(
                        400,
                        f'Property "{camel}" does not have accessor method "get{camel}" '
                        f'in class "{_INTERFACE[kind]}".',
                    )
                continue
            if key in ("creation_time", "update_time"):
                continue  # Magento regenerates these on save
            if key in ("active", "is_active"):
                data["active"] = value in (True, 1, "1", "true", "True")
            elif key == "id":
                data["id"] = _int(value)
            elif key == "store_id":
                data["store_id"] = [_int(s) for s in (value if isinstance(value, list) else [value])]
            else:
                data[key] = value
        return data

    def _check_unique(self, kind: str, entity_id: Optional[int], merged: Dict[str, Any]) -> None:
        identifier = merged.get("identifier")
        stores = set(merged.get("store_id") or [0])
        for other_id, other in self._store(kind).items():
            if other_id == entity_id or other["identifier"] != identifier:
                continue
            other_stores = set(other.get("store_id") or [0])
            if 0 in stores or 0 in other_stores or stores & other_stores:
                if kind == "block":
                    raise MagentoError(400, "A block identifier with the same properties already exists in the selected store.")
                raise MagentoError(400, "Could not save the page: A page URL key for specified store already exists.")

    def _save(self, kind: str, payload: Any) -> Dict[str, Any]:
        store = self._store(kind)
        data = self._normalize_input(payload, kind)
        entity_id = data.pop("id", None)
        existing = store.get(entity_id) if entity_id is not None else None

        if entity_id is not None and existing is None:
            # AbstractDb::save() takes the UPDATE path when an id is set; the row does not
            # exist, so the store-link insert then violates the cms_*_store foreign key.
            raise MagentoError(
                400,
                f"Could not save the {kind}: SQLSTATE[23000]: Integrity constraint violation: "
                f"1452 Cannot add or update a child row: a foreign key constraint fails "
                f"(`cms_{kind}_store`, CONSTRAINT `CMS_{kind.upper()}_STORE_{kind.upper()}_ID_"
                f"CMS_{kind.upper()}_{kind.upper()}_ID`)",
            )
        merged = {**(existing or self._defaults(kind)), **data}
        if not merged.get("identifier"):
            raise MagentoError(400, f"Could not save the {kind}: Column 'identifier' cannot be null")
        self._check_unique(kind, entity_id, merged)

        if existing is not None:
            existing.update(data)
            existing["update_time"] = self.clock()
            return self._public(existing, kind)
        return self._insert(kind, data)

    def _get(self, kind: str, entity_id: int) -> Dict[str, Any]:
        entity = self._store(kind).get(entity_id)
        if entity is None:
            raise MagentoError(404, f'The CMS {kind} with the "%1" ID doesn\'t exist.', [str(entity_id)])
        return self._public(entity, kind)

    def _search(self, kind: str, params: Dict[str, str]) -> Dict[str, Any]:
        if not any(k.startswith("searchCriteria") for k in params):
            raise MagentoError(400, "%fieldName is a required field.", {"fieldName": "searchCriteria"})

        groups: Dict[int, Dict[int, Dict[str, str]]] = {}
        for key, value in params.items():
            match = _FILTER_KEY.match(key)
            if match:
                g, f, part = int(match.group(1)), int(match.group(2)), match.group(3)
                groups.setdefault(g, {}).setdefault(f, {})[part] = value

        columns = _FILTER_COLUMNS[kind]
        for group in groups.values():
            for flt in group.values():
                if flt.get("field") and flt["field"] not in columns:
                    # Unknown column: the SQL error surfaces as Magento's generic 500.
                    raise MagentoError(500, "Internal Error. Details are available in Magento log file. "
                                            "Report ID: webapi-stub-unknown-column")
        entities = [e for _, e in sorted(self._store(kind).items())]
        for group in groups.values():
            filters = list(group.values())
            entities = [e for e in entities if any(_matches(e, f, columns) for f in filters)]
        items = [self._public(e, kind) for e in entities]
        total = len(items)

        page_size = _int(params.get("searchCriteria[pageSize]", 0) or 0)
        current_page = _int(params.get("searchCriteria[currentPage]", 1) or 1)
        echo: Dict[str, Any] = {"filter_groups": [
            {"filters": [{"field": f.get("field"), "value": f.get("value"),
                          "condition_type": f.get("condition_type", "eq")} for f in g.values()]}
            for g in groups.values()]}
        if page_size > 0:
            last_page = max(1, math.ceil(total / page_size))
            current_page = min(max(current_page, 1), last_page)  # Magento clamps, never empty
            items = items[(current_page - 1) * page_size: current_page * page_size]
            echo["page_size"] = page_size
        if "searchCriteria[currentPage]" in params:
            echo["current_page"] = current_page
        return {"items": items, "search_criteria": echo, "total_count": total}

    def _authorize(self, request: Request, resource: str) -> None:
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or token not in self.tokens:
            raise MagentoError(401, "The consumer isn't authorized to access %resources.", {"resources": resource})

    def _record(self, request: Request, body: Any = None) -> None:
        self.requests.append(RecordedRequest(request.method, request.url.path, dict(request.query_params), body))


def _sql_like_to_regex(pattern: str) -> re.Pattern:
    """Translate a SQL LIKE pattern (``%`` any run, ``_`` one char, ``\\`` escapes) to a regex."""
    out, i = [], 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\" and i + 1 < len(pattern):
            out.append(re.escape(pattern[i + 1]))
            i += 2
            continue
        out.append(".*" if ch == "%" else "." if ch == "_" else re.escape(ch))
        i += 1
    return re.compile("^" + "".join(out) + "$", re.IGNORECASE | re.DOTALL)


def _column_value(entity: Dict[str, Any], column: str) -> Any:
    """Value as the database column would hold it: booleans are tinyint 0/1."""
    value = entity.get(column)
    return int(value) if isinstance(value, bool) else value


def _matches(entity: Dict[str, Any], flt: Dict[str, str], columns: Dict[str, str]) -> bool:
    fld = flt.get("field")
    if not fld:
        return True
    column = columns[fld]
    wanted = flt.get("value", "")
    cond = flt.get("condition_type", "eq")
    if column == "store_id":
        # cms_*_store join: a row matches when it is linked to the store
        stores = [str(s) for s in (entity.get("store_id") or [0])]
        if cond == "eq":
            return wanted in stores
        if cond == "in":
            return any(v.strip() in stores for v in wanted.split(","))
        raise MagentoError(400, f'Condition type "{cond}" is not supported for store_id by the stub.')
    actual = _column_value(entity, column)
    actual_s = "" if actual is None else str(actual)
    if cond == "eq":
        return actual_s == wanted
    if cond == "neq":
        return actual_s != wanted
    if cond == "like":
        return _sql_like_to_regex(wanted).match(actual_s) is not None
    if cond == "nlike":
        return _sql_like_to_regex(wanted).match(actual_s) is None
    if cond == "in":
        return actual_s in [v.strip() for v in wanted.split(",")]
    if cond == "nin":
        return actual_s not in [v.strip() for v in wanted.split(",")]
    if cond == "null":
        return actual is None
    if cond == "notnull":
        return actual is not None
    raise MagentoError(400, f'Condition type "{cond}" is not supported by the stub.')


def create_app(magento: FakeMagento) -> FastAPI:
    """Build the ASGI app serving ``magento``'s state under /rest/V1 (and /rest/<store>/V1)."""
    app = FastAPI(title=f"Fake Magento ({magento.name})", docs_url=None, redoc_url=None, openapi_url=None)
    router = APIRouter()

    async def _json_body(request: Request) -> Any:
        try:
            return await request.json()
        except ValueError:
            raise MagentoError(400, "Decoding error.")

    @router.get("/store/storeViews")
    async def store_views(request: Request) -> List[Dict[str, Any]]:
        magento._record(request)
        magento._authorize(request, "Magento_Backend::store")
        return magento.store_views

    def _register(kind: str, segment: str, read_resource: str, write_resource: str) -> None:
        @router.get(f"/{segment}/search", name=f"{kind}_search")
        async def search(request: Request) -> Dict[str, Any]:
            magento._record(request)
            magento._authorize(request, read_resource)
            return magento._search(kind, dict(request.query_params))

        @router.get(f"/{segment}/{{entity_id}}", name=f"{kind}_get")
        async def get_one(entity_id: int, request: Request) -> Dict[str, Any]:
            magento._record(request)
            magento._authorize(request, read_resource)
            return magento._get(kind, entity_id)

        @router.post(f"/{segment}", name=f"{kind}_create")
        async def create(request: Request) -> Dict[str, Any]:
            body = await _json_body(request)
            magento._record(request, body)
            magento._authorize(request, write_resource)
            return magento._save(kind, (body or {}).get(kind) if isinstance(body, dict) else None)

        @router.put(f"/{segment}/{{entity_id}}", name=f"{kind}_update")
        async def update(entity_id: int, request: Request) -> Dict[str, Any]:
            body = await _json_body(request)
            magento._record(request, body)
            magento._authorize(request, write_resource)
            # Magento ignores the URL id: the body decides which entity is saved.
            return magento._save(kind, (body or {}).get(kind) if isinstance(body, dict) else None)

    _register("block", "cmsBlock", "Magento_Cms::block", "Magento_Cms::block")
    _register("page", "cmsPage", "Magento_Cms::page", "Magento_Cms::save")

    for prefix in ("/rest/V1", "/rest/all/V1", "/rest/default/V1"):
        app.include_router(router, prefix=prefix)

    @app.middleware("http")
    async def inject_faults(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        fault = magento._take_fault(request.method, request.url.path)
        if fault is not None:
            magento._record(request)
            return JSONResponse(status_code=fault.status, content={"message": fault.message})
        return await call_next(request)

    @app.exception_handler(MagentoError)
    async def magento_error(_: Request, exc: MagentoError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=exc.body())

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        return JSONResponse(status_code=400, content={
            "message": f'Invalid type for value: "{first.get("input")}". Expected Type: "int".'})

    @app.exception_handler(404)
    async def not_found(request: Request, _: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={
            "message": "Request does not match any route.",
            "parameters": {"route": request.url.path}})

    app.state.magento = magento
    return app
