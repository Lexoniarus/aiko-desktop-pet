"""Anonymous learned aggregates and bounded quiet phases, without raw samples."""

ADAPTIVE_SCHEMA = (
    """CREATE TABLE adaptive_state (
        id INTEGER PRIMARY KEY REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(id = 1),
        last_slot_key TEXT NOT NULL, profile_day TEXT NOT NULL,
        strain REAL NOT NULL CHECK(strain >= 0),
        settled_work REAL NOT NULL CHECK(settled_work >= 0),
        session_seconds REAL NOT NULL CHECK(session_seconds >= 0),
        rest_seconds REAL NOT NULL CHECK(rest_seconds >= 0),
        last_session_seconds REAL NOT NULL CHECK(last_session_seconds >= 0),
        last_work_wall REAL NOT NULL CHECK(last_work_wall >= 0),
        last_contact_wall REAL NOT NULL CHECK(last_contact_wall >= 0),
        last_seen_wall REAL NOT NULL CHECK(last_seen_wall >= 0),
        quiet_start REAL NOT NULL CHECK(quiet_start >= 0 AND quiet_start < 1440),
        quiet_end REAL NOT NULL CHECK(quiet_end >= 0 AND quiet_end < 1440),
        quiet_adjusted_day TEXT NOT NULL
    )""",
    """CREATE TABLE adaptive_hour_slots (
        slot INTEGER PRIMARY KEY CHECK(slot BETWEEN 0 AND 167),
        state_id INTEGER NOT NULL REFERENCES adaptive_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        hour_seconds REAL NOT NULL CHECK(hour_seconds >= 0),
        busy_seconds REAL NOT NULL CHECK(busy_seconds >= 0),
        present_seconds REAL NOT NULL CHECK(present_seconds >= 0),
        observed_days REAL NOT NULL CHECK(observed_days >= 0)
    )""",
    """CREATE TABLE adaptive_quiet_phases (
        day TEXT PRIMARY KEY NOT NULL,
        state_id INTEGER NOT NULL REFERENCES adaptive_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        start REAL NOT NULL CHECK(start >= 0 AND start < 1440),
        end REAL NOT NULL CHECK(end >= 0 AND end < 1440)
    )""",
)
