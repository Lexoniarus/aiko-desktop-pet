"""Original wish goals, shared lifecycle anchors and bounded round evidence."""

WISH_SCHEMA = (
    """CREATE TABLE wish_state (
        id INTEGER PRIMARY KEY REFERENCES pet_state(id) ON DELETE CASCADE CHECK(id = 1),
        next_instance_id INTEGER NOT NULL CHECK(next_instance_id > 0),
        last_created_by_area TEXT NOT NULL,
        last_expressed_at REAL CHECK(last_expressed_at >= 0),
        refresh_at REAL CHECK(refresh_at >= 0)
    )""",
    """CREATE TABLE wish_instances (
        instance_id INTEGER PRIMARY KEY CHECK(instance_id > 0),
        state_id INTEGER NOT NULL REFERENCES wish_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        definition_id TEXT NOT NULL,
        area TEXT NOT NULL CHECK(area IN ('food', 'games', 'social', 'affection')),
        objective_id TEXT NOT NULL,
        required_count INTEGER NOT NULL CHECK(required_count BETWEEN 0 AND 100),
        target_explicit INTEGER NOT NULL CHECK(target_explicit IN (0, 1)),
        target_kind TEXT CHECK(target_kind IN ('food', 'game', 'social', 'care')),
        target_mode TEXT CHECK(target_mode IN ('exact', 'any', 'exclude')),
        target_id TEXT,
        created_at REAL NOT NULL CHECK(created_at >= 0),
        expires_at REAL NOT NULL CHECK(expires_at > created_at),
        expressed_at REAL CHECK(expressed_at >= created_at),
        pinned INTEGER NOT NULL CHECK(pinned IN (0, 1)),
        completed_rounds INTEGER NOT NULL CHECK(completed_rounds >= 0),
        wins INTEGER NOT NULL CHECK(wins >= 0),
        losses INTEGER NOT NULL
            CHECK(losses >= 0 AND wins + losses <= completed_rounds),
        session_id TEXT CHECK(length(session_id) BETWEEN 1 AND 128),
        CHECK((target_explicit = 0 AND target_kind IS NULL AND target_mode IS NULL
               AND target_id IS NOT NULL AND length(target_id) > 0)
           OR (target_explicit = 1 AND target_kind IS NOT NULL
               AND target_mode IS NOT NULL
               AND ((target_mode = 'any' AND target_id IS NULL)
                 OR (target_mode IN ('exact', 'exclude') AND target_id IS NOT NULL
                     AND length(target_id) > 0))))
    )""",
    """CREATE TABLE wish_round_receipts (
        wish_id INTEGER NOT NULL REFERENCES wish_instances(instance_id)
            ON DELETE CASCADE,
        position_index INTEGER NOT NULL CHECK(position_index >= 0),
        round_signature TEXT NOT NULL CHECK(length(round_signature) BETWEEN 1 AND 128),
        PRIMARY KEY(wish_id, position_index), UNIQUE(wish_id, round_signature)
    )""",
)
