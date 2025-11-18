import pytest

from src.ai_doctor.db import init_db, create_session, save_message, fetch_messages


def _can_run():
    # Basic heuristic: allow skip if host unreachable credentials likely missing.
    return True  # rely on init_db exception for skip decision


@pytest.mark.order(1)
def test_db_flow_insert_and_fetch():
    if not _can_run():
        pytest.skip("Environment not suitable for DB test")
    try:
        init_db()
    except Exception as e:
        pytest.skip(f"Skipping: cannot initialize DB ({e})")

    session_uuid = create_session()
    save_message(session_uuid, "patient", "Unit test patient message", None)
    save_message(session_uuid, "doctor", "Unit test doctor response", None)
    rows = fetch_messages(session_uuid)
    assert len(rows) >= 2, "Expected at least two messages inserted"
    roles = {r[0] for r in rows}
    assert {"patient", "doctor"}.issubset(roles), f"Roles missing in rows: {roles}"


@pytest.mark.order(2)
def test_db_flow_additional_message():
    try:
        init_db()
    except Exception as e:
        pytest.skip(f"Skipping: cannot initialize DB ({e})")
    session_uuid = create_session()
    save_message(session_uuid, "patient", "Follow-up message", None)
    rows = fetch_messages(session_uuid)
    assert any(r[1] == "Follow-up message" for r in rows), "Inserted follow-up message not found"