"""Bounded relationship evidence and the existing per-need exposure timeline."""

RELATIONSHIP_SCHEMA = (
    """CREATE TABLE relationship_state (
        id INTEGER PRIMARY KEY REFERENCES pet_state(id) ON DELETE CASCADE CHECK(id = 1),
        baseline REAL CHECK(baseline >= 0),
        last_contact REAL CHECK(last_contact >= 0),
        continuous_since REAL CHECK(continuous_since >= 0),
        eligible TEXT NOT NULL
    )""",
    """CREATE TABLE relationship_entries (
        state_id INTEGER NOT NULL REFERENCES relationship_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        entry_kind TEXT NOT NULL CHECK(entry_kind IN ('reward', 'penalty')),
        position INTEGER NOT NULL CHECK(position >= 0),
        occurred_at REAL NOT NULL CHECK(occurred_at >= 0),
        kind TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount > 0 AND amount <= 100),
        PRIMARY KEY(entry_kind, position)
    )""",
    """CREATE TABLE need_exposure_buckets (
        state_id INTEGER NOT NULL REFERENCES relationship_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        need TEXT NOT NULL
            CHECK(need IN ('satiety','energy','fun','social','affection')),
        start REAL NOT NULL CHECK(start >= 0),
        width REAL NOT NULL CHECK(width > 0),
        critical REAL NOT NULL CHECK(critical >= 0 AND critical <= width + 1e-7),
        zero REAL NOT NULL CHECK(zero >= 0 AND zero <= critical + 1e-8),
        PRIMARY KEY(need, start)
    )""",
)
