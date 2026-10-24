"""Bounded content receipts and provider wall-clock budgets, without buffers."""

SOCIAL_SCHEMA = (
    """CREATE TABLE social_receipts (
        position_index INTEGER PRIMARY KEY CHECK(position_index >= 0),
        state_id INTEGER NOT NULL REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        category TEXT NOT NULL CHECK(category <> 'horoscope'),
        identity TEXT NOT NULL UNIQUE, fingerprint TEXT NOT NULL UNIQUE
    )""",
    """CREATE TABLE social_requests (
        position_index INTEGER PRIMARY KEY CHECK(position_index >= 0),
        state_id INTEGER NOT NULL REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        provider TEXT NOT NULL,
        attempted_at REAL NOT NULL CHECK(attempted_at >= 0)
    )""",
    """CREATE TABLE provider_pauses (
        provider TEXT PRIMARY KEY NOT NULL,
        state_id INTEGER NOT NULL REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        pause_until REAL NOT NULL CHECK(pause_until >= 0)
    )""",
)
