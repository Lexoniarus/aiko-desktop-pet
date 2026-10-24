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
