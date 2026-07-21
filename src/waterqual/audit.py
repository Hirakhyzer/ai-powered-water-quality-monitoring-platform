"""Hash-chained audit ledger for synthetic water-quality reviews."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


def _hash_record(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def append_record(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Append one hash-chained audit record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = "genesis"
    if path.exists() and path.read_text(encoding="utf-8").strip():
        last_line = path.read_text(encoding="utf-8").strip().splitlines()[-1]
        previous_hash = json.loads(last_line)["record_hash"]
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "previous_hash": previous_hash,
        "payload": payload,
    }
    record["record_hash"] = _hash_record(record)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return record


def verify_log(path: str | Path) -> dict[str, Any]:
    """Verify the hash chain."""
    path = Path(path)
    if not path.exists():
        return {"valid": True, "records": 0, "last_hash": "genesis"}
    previous = "genesis"
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        expected_hash = record.pop("record_hash")
        if record.get("previous_hash") != previous:
            return {"valid": False, "records": count, "last_hash": previous, "error": "previous hash mismatch"}
        actual_hash = _hash_record(record)
        if actual_hash != expected_hash:
            return {"valid": False, "records": count, "last_hash": previous, "error": "record hash mismatch"}
        previous = expected_hash
        count += 1
    return {"valid": True, "records": count, "last_hash": previous}
