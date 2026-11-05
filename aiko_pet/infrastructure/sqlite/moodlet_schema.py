"""Episode-owned stages/causes and shared optional care-history metadata."""

MOODLET_SCHEMA = (
    """CREATE TABLE moodlet_state (
        id INTEGER PRIMARY KEY REFERENCES pet_state(id) ON DELETE CASCADE CHECK(id = 1),
        baseline REAL NOT NULL CHECK(baseline >= 0),
        next_instance_id INTEGER NOT NULL CHECK(next_instance_id > 0),
        poor_care_baseline REAL CHECK(poor_care_baseline >= 0),
        care_evidence_baseline REAL CHECK(care_evidence_baseline >= 0),
        next_encounter_id INTEGER CHECK(next_encounter_id > 0),
        next_experience_id INTEGER CHECK(next_experience_id > 0),
        CHECK((care_evidence_baseline IS NULL AND next_encounter_id IS NULL
               AND next_experience_id IS NULL)
           OR (care_evidence_baseline IS NOT NULL AND next_encounter_id IS NOT NULL
               AND next_experience_id IS NOT NULL))
    )""",
    """CREATE TABLE moodlet_episodes (
        instance_id INTEGER PRIMARY KEY CHECK(instance_id > 0),
        state_id INTEGER NOT NULL REFERENCES moodlet_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        definition_id TEXT NOT NULL UNIQUE,
        level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 3),
        started_at REAL NOT NULL CHECK(started_at >= 0),
        last_trigger_at REAL NOT NULL CHECK(last_trigger_at >= started_at),
        remaining_seconds REAL NOT NULL CHECK(remaining_seconds >= 0),
        lower_stages_explicit INTEGER NOT NULL CHECK(lower_stages_explicit IN (0, 1)),
        pending_repetitions INTEGER NOT NULL CHECK(pending_repetitions >= 0),
        decay_paused INTEGER NOT NULL CHECK(decay_paused IN (0, 1)),
        recovery_since REAL CHECK(recovery_since >= started_at),
        attribution TEXT NOT NULL CHECK(attribution IN ('user','autonomous','unknown'))
    )""",
    """CREATE TABLE moodlet_stage_state (
        episode_id INTEGER NOT NULL REFERENCES moodlet_episodes(instance_id)
            ON DELETE CASCADE,
        stage INTEGER NOT NULL CHECK(stage BETWEEN 1 AND 3),
        lower_remaining_seconds REAL CHECK(lower_remaining_seconds >= 0),
        relief_position INTEGER CHECK(relief_position >= 0),
        PRIMARY KEY(episode_id, stage), UNIQUE(episode_id, relief_position),
        CHECK(lower_remaining_seconds IS NOT NULL OR relief_position IS NOT NULL)
    )""",
    """CREATE TABLE moodlet_causes (
        cause_id INTEGER PRIMARY KEY,
        episode_id INTEGER NOT NULL REFERENCES moodlet_episodes(instance_id)
            ON DELETE CASCADE,
        position_index INTEGER NOT NULL CHECK(position_index BETWEEN 0 AND 2),
        kind TEXT NOT NULL,
        occurred_at REAL NOT NULL CHECK(occurred_at >= 0),
        event_id TEXT,
        attribution TEXT NOT NULL CHECK(attribution IN ('user','autonomous','unknown')),
        target_id TEXT, outcome TEXT NOT NULL, object_id TEXT,
        handed_over_at REAL
            CHECK(handed_over_at >= 0 AND handed_over_at <= occurred_at),
        source_wish_instance_id INTEGER CHECK(source_wish_instance_id > 0),
        wish_snapshot TEXT, details_snapshot TEXT NOT NULL,
        UNIQUE(episode_id, position_index),
        CHECK((source_wish_instance_id IS NULL) = (wish_snapshot IS NULL))
    )""",
    """CREATE UNIQUE INDEX moodlet_cause_semantic_receipt
        ON moodlet_causes(episode_id, kind, event_id,
                         coalesce(source_wish_instance_id, -1))
        WHERE event_id IS NOT NULL""",
)
