"""Actual ground stock and independently acquired subjective memory records."""

WORLD_SCHEMA = (
    """CREATE TABLE world_state (
        id INTEGER PRIMARY KEY REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(id = 1),
        width REAL NOT NULL CHECK(width > 0), height REAL NOT NULL CHECK(height > 0),
        ground_inset REAL NOT NULL
            CHECK(ground_inset >= 0 AND ground_inset <= width / 2),
        revision INTEGER NOT NULL CHECK(revision >= 0),
        next_instance_id INTEGER NOT NULL CHECK(next_instance_id > 0)
    )""",
    """CREATE TABLE world_objects (
        instance_id TEXT PRIMARY KEY NOT NULL,
        world_id INTEGER NOT NULL REFERENCES world_state(id) ON DELETE CASCADE
            CHECK(world_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        definition_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision >= 0),
        x REAL NOT NULL CHECK(x >= 0),
        footprint_left REAL NOT NULL CHECK(footprint_left >= 0),
        footprint_right REAL NOT NULL CHECK(footprint_right >= 0)
    )""",
    """CREATE TABLE object_memory_state (
        id INTEGER PRIMARY KEY REFERENCES world_state(id) ON DELETE CASCADE
            CHECK(id = 1),
        next_record_id INTEGER NOT NULL CHECK(next_record_id > 0),
        world_next_id INTEGER NOT NULL CHECK(world_next_id > 0)
    )""",
    """CREATE TABLE object_memories (
        token TEXT PRIMARY KEY NOT NULL,
        memory_id INTEGER NOT NULL REFERENCES object_memory_state(id) ON DELETE CASCADE
            CHECK(memory_id = 1),
        position_index INTEGER NOT NULL UNIQUE CHECK(position_index >= 0),
        identity TEXT, kind TEXT CHECK(kind IN ('food', 'drink')),
        x REAL NOT NULL CHECK(x >= 0), height REAL NOT NULL CHECK(height >= 0),
        resting INTEGER NOT NULL CHECK(resting IN (0, 1)),
        age_seconds REAL NOT NULL CHECK(age_seconds >= 0),
        assessed INTEGER NOT NULL CHECK(assessed IN (0, 1)),
        disposition TEXT CHECK(disposition IN ('deferred', 'interrupted')),
        place_status TEXT NOT NULL
            CHECK(place_status IN ('remembered', 'missing', 'superseded')),
        instance_id TEXT UNIQUE,
        CHECK((identity IS NULL) = (kind IS NULL))
    )""",
    """CREATE TABLE object_memory_sources (
        token TEXT NOT NULL REFERENCES object_memories(token) ON DELETE CASCADE,
        source_token TEXT NOT NULL REFERENCES object_memories(token) ON DELETE CASCADE,
        position_index INTEGER NOT NULL CHECK(position_index >= 0),
        PRIMARY KEY(token, source_token), UNIQUE(token, position_index),
        CHECK(token <> source_token)
    )""",
)
