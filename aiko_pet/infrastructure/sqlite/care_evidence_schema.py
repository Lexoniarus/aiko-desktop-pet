"""Shared bounded care receipts with independent per-family processing state."""

CARE_EVIDENCE_SCHEMA = (
    """CREATE TABLE care_encounters (
        instance_id INTEGER PRIMARY KEY CHECK(instance_id > 0),
        state_id INTEGER NOT NULL REFERENCES moodlet_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        started_at REAL NOT NULL CHECK(started_at >= 0),
        last_activity_at REAL NOT NULL CHECK(last_activity_at >= started_at)
    )""",
    """CREATE TABLE care_evidence (
        receipt_id TEXT PRIMARY KEY NOT NULL
            CHECK(length(receipt_id) BETWEEN 1 AND 128),
        state_id INTEGER NOT NULL REFERENCES moodlet_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        occurred_at REAL NOT NULL CHECK(occurred_at >= 0),
        activity TEXT NOT NULL, outcome TEXT NOT NULL,
        area TEXT, target_kind TEXT, target_id TEXT,
        encounter_id INTEGER REFERENCES care_encounters(instance_id),
        wish_instance_id INTEGER CHECK(wish_instance_id > 0),
        pleasant INTEGER NOT NULL CHECK(pleasant IN (0, 1)),
        upsetting INTEGER NOT NULL CHECK(upsetting IN (0, 1)),
        boundary_violated INTEGER NOT NULL CHECK(boundary_violated IN (0, 1)),
        object_id TEXT,
        CHECK((target_kind IS NULL) = (target_id IS NULL)),
        CHECK(pleasant + upsetting <= 1 AND boundary_violated <= upsetting)
    )""",
    """CREATE TABLE long_term_progress (
        definition_id TEXT PRIMARY KEY NOT NULL,
        state_id INTEGER NOT NULL REFERENCES moodlet_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        period_start REAL NOT NULL CHECK(period_start >= 0),
        processed_until REAL NOT NULL
            CHECK(processed_until >= 0 AND processed_until <= period_start),
        last_accounted_at REAL NOT NULL CHECK(last_accounted_at >= period_start),
        awake_contact_gap_seconds REAL NOT NULL CHECK(awake_contact_gap_seconds >= 0),
        longest_awake_contact_gap_seconds REAL NOT NULL
            CHECK(longest_awake_contact_gap_seconds >= 0)
    )""",
)
