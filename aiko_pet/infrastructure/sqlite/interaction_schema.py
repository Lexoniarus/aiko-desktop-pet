"""Existing interaction boundaries and per-need emotional processing cursors."""

INTERACTION_SCHEMA = (
    """CREATE TABLE interaction_state (
        id INTEGER PRIMARY KEY REFERENCES moodlet_state(id) ON DELETE CASCADE
            CHECK(id = 1),
        poke_boundary_at REAL CHECK(poke_boundary_at >= 0),
        petting_boundary_at REAL CHECK(petting_boundary_at >= 0),
        petting_refused_until REAL NOT NULL CHECK(petting_refused_until >= 0),
        petting_excess_attempts INTEGER NOT NULL CHECK(petting_excess_attempts >= 0),
        petting_last_excess_at REAL CHECK(petting_last_excess_at >= 0),
        food_id TEXT,
        request_pending INTEGER NOT NULL CHECK(request_pending IN (0, 1)),
        requested_at REAL CHECK(requested_at >= 0),
        ignored_portions INTEGER NOT NULL CHECK(ignored_portions >= 0)
    )""",
    """CREATE TABLE food_intake_receipts (
        state_id INTEGER NOT NULL REFERENCES interaction_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER PRIMARY KEY CHECK(position_index >= 0),
        occurred_at REAL NOT NULL CHECK(occurred_at >= 0)
    )""",
    """CREATE TABLE poor_care_cursors (
        need TEXT PRIMARY KEY NOT NULL
            CHECK(need IN ('satiety','energy','fun','social','affection')),
        state_id INTEGER NOT NULL REFERENCES moodlet_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        accounted_at REAL NOT NULL CHECK(accounted_at >= 0),
        accounted_critical REAL NOT NULL CHECK(accounted_critical >= 0),
        accounted_zero REAL NOT NULL
            CHECK(accounted_zero >= 0 AND accounted_zero <= accounted_critical),
        handled_at REAL NOT NULL CHECK(handled_at >= accounted_at),
        handled_critical REAL NOT NULL CHECK(handled_critical >= 0),
        handled_zero REAL NOT NULL
            CHECK(handled_zero >= 0 AND handled_zero <= handled_critical),
        handled_level INTEGER NOT NULL CHECK(handled_level BETWEEN 0 AND 3),
        exposed INTEGER NOT NULL CHECK(exposed IN (0, 1))
    )""",
)
