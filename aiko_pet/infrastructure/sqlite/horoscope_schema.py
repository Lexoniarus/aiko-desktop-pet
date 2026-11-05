"""One bounded calendar-day episode with its original text and continuation."""

HOROSCOPE_SCHEMA = (
    """CREATE TABLE horoscope_days (
        day TEXT PRIMARY KEY NOT NULL,
        state_id INTEGER NOT NULL UNIQUE REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        attempts INTEGER NOT NULL CHECK(attempts BETWEEN 0 AND 3),
        progress_index INTEGER NOT NULL CHECK(progress_index BETWEEN 0 AND 12),
        admitted INTEGER NOT NULL CHECK(admitted IN (0, 1)),
        completed INTEGER NOT NULL CHECK(completed IN (0, 1)),
        sign TEXT, reading_date TEXT, overview TEXT,
        advice TEXT, disclaimer TEXT, footer TEXT,
        CHECK((sign IS NULL AND reading_date IS NULL AND overview IS NULL
               AND advice IS NULL AND disclaimer IS NULL AND footer IS NULL
               AND progress_index = 0 AND admitted = 0 AND completed = 0)
           OR (sign IS NOT NULL AND reading_date IS NOT NULL AND overview IS NOT NULL
               AND advice IS NOT NULL AND disclaimer IS NOT NULL AND footer IS NOT NULL
               AND reading_date = day AND attempts > 0)),
        CHECK(admitted = 1 OR (progress_index = 0 AND completed = 0))
    )""",
)


LOCAL_HOROSCOPE_SCHEMA = (
    """CREATE TABLE local_horoscope_days (
        day TEXT PRIMARY KEY NOT NULL,
        state_id INTEGER NOT NULL REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(state_id = 1),
        sign TEXT, progress_index INTEGER NOT NULL
            CHECK(progress_index BETWEEN 0 AND 40),
        admitted INTEGER NOT NULL CHECK(admitted IN (0, 1)),
        completed INTEGER NOT NULL CHECK(completed IN (0, 1)),
        book_id TEXT UNIQUE, first_put_down_at REAL CHECK(first_put_down_at >= 0),
        entry_id TEXT, entry_revision INTEGER CHECK(entry_revision > 0),
        catalogue_revision INTEGER CHECK(catalogue_revision > 0),
        reaction_id TEXT, comment_id TEXT,
        sky_instant TEXT, sun_longitude REAL, moon_longitude REAL,
        phase_degrees REAL, engine_version TEXT,
        CHECK(completed = 0 OR admitted = 1)
    )""",
    """CREATE TABLE local_horoscope_cues (
        day TEXT NOT NULL REFERENCES local_horoscope_days(day) ON DELETE CASCADE,
        position_index INTEGER NOT NULL CHECK(position_index BETWEEN 0 AND 39),
        kind TEXT NOT NULL CHECK(kind IN ('text', 'emote', 'pause')),
        content TEXT NOT NULL,
        duration_ms INTEGER NOT NULL CHECK(duration_ms BETWEEN 250 AND 10000),
        PRIMARY KEY(day, position_index),
        CHECK(kind <> 'text' OR length(content) BETWEEN 1 AND 125)
    )""",
)
