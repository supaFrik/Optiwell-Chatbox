"""Standalone DB flow verification script.

Runs init_db, inserts patient & doctor messages, then fetches and prints them.
Exit code 0 on success, non-zero on failure.
"""
from src.ai_doctor.db import init_db, create_session, save_message, fetch_messages


def main():
    try:
        init_db()
    except Exception as e:
        print(f"[FAIL] init_db error: {e}")
        raise SystemExit(1)
    sid = create_session()
    try:
        save_message(sid, "patient", "Verification patient message", None)
        save_message(sid, "doctor", "Verification doctor response", None)
        rows = fetch_messages(sid)
    except Exception as e:
        print(f"[FAIL] message insert/fetch error: {e}")
        raise SystemExit(1)
    roles = {r[0] for r in rows}
    if {"patient", "doctor"}.issubset(roles):
        print(f"[OK] Session {sid} stored {len(rows)} messages. Roles present: {roles}")
        for role, content in rows:
            print(f" - {role}: {content[:80]}")
        raise SystemExit(0)
    else:
        print(f"[FAIL] Expected both roles; got {roles}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()