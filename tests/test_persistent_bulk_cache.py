import uuid
from thingsbridge.cache import ShelveCache
import thingsbridge.bulk_tools as bulk
from thingsbridge.applescript import AppleScriptResult


def test_create_bulk_cache_persistence(monkeypatch, tmp_path):
    cache_path = tmp_path / "bulk.db"
    cache = ShelveCache(str(cache_path))
    monkeypatch.setattr(bulk, "_CREATE_BULK_CACHE", cache)

    monkeypatch.setattr(bulk.client, "ensure_running", lambda: None)
    monkeypatch.setattr(
        bulk.client.executor,
        "execute",
        lambda script: AppleScriptResult(True, "A1,B2", None),
    )

    key = uuid.uuid4().hex
    items = [{"title": "A"}, {"title": "B"}]

    first = bulk.create_todo_bulk(idempotency_key=key, items=items)
    cache.close()
    cache2 = ShelveCache(str(cache_path))
    monkeypatch.setattr(bulk, "_CREATE_BULK_CACHE", cache2)
    second = bulk.create_todo_bulk(idempotency_key=key, items=items)
    cache2.close()

    assert first == second
