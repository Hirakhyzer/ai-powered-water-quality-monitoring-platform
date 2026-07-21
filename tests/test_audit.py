from waterqual.audit import append_record, verify_log


def test_hash_chained_audit_log(tmp_path):
    path = tmp_path / "audit.jsonl"
    append_record(path, {"event": "first"})
    append_record(path, {"event": "second"})
    result = verify_log(path)
    assert result["valid"] is True
    assert result["records"] == 2
