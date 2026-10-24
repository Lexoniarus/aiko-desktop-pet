"""Bounded handover facts outlive source wishes and actual World stock."""

FOOD_HANDOVER_SCHEMA = (
    """CREATE TABLE food_handover_receipts (
        handover_id TEXT PRIMARY KEY NOT NULL
            CHECK(length(handover_id) BETWEEN 1 AND 128),
        state_id INTEGER NOT NULL REFERENCES wish_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        object_id TEXT NOT NULL CHECK(length(object_id) BETWEEN 1 AND 128),
        handed_over_at REAL NOT NULL CHECK(handed_over_at >= 0),
        wish_context TEXT NOT NULL,
        recognized_food_id TEXT,
        recognized_at REAL CHECK(recognized_at >= handed_over_at),
        status TEXT NOT NULL CHECK(status IN ('pending', 'evaluated', 'cancelled')),
        resolved_wish_instance_id INTEGER CHECK(resolved_wish_instance_id > 0),
        accounted_wish_ids TEXT NOT NULL,
        CHECK((recognized_food_id IS NULL) = (recognized_at IS NULL)),
        CHECK(status <> 'pending' OR recognized_food_id IS NULL),
        CHECK(status <> 'evaluated' OR recognized_food_id IS NOT NULL)
    )""",
    """CREATE UNIQUE INDEX one_pending_food_handover_per_object
        ON food_handover_receipts(object_id) WHERE status = 'pending'""",
)
