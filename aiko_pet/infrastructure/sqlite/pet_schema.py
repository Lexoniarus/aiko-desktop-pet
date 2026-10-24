"""Version-one columns for core Pet values, sleep and application settings."""

PET_SCHEMA = (
    """CREATE TABLE pet_state (
        id INTEGER PRIMARY KEY REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(id = 1),
        satiety REAL NOT NULL CHECK(satiety BETWEEN 0 AND 100),
        energy REAL NOT NULL CHECK(energy BETWEEN 0 AND 100),
        fun REAL NOT NULL CHECK(fun BETWEEN 0 AND 100),
        social REAL NOT NULL CHECK(social BETWEEN 0 AND 100),
        affection REAL NOT NULL CHECK(affection BETWEEN 0 AND 100),
        mood REAL NOT NULL CHECK(mood BETWEEN 0 AND 100),
        friendship REAL NOT NULL CHECK(friendship BETWEEN 0 AND 100),
        friendship_day TEXT NOT NULL,
        friendship_gained_today REAL NOT NULL CHECK(friendship_gained_today >= 0),
        care_types_today TEXT NOT NULL, care_last_rewards TEXT NOT NULL,
        sleeping INTEGER NOT NULL CHECK(sleeping IN (0, 1)),
        meals_date TEXT NOT NULL, meals_today TEXT NOT NULL,
        sleep_origin TEXT NOT NULL CHECK(sleep_origin IN ('', 'routine','manual',
                                                        'nap','recovery')),
        auto_sleep_night TEXT NOT NULL, nap_until REAL NOT NULL CHECK(nap_until >= 0),
        auto_nap_day TEXT NOT NULL,
        remaining_digest_minutes REAL NOT NULL CHECK(remaining_digest_minutes >= 0),
        awake_hours_since_last_food REAL NOT NULL
            CHECK(awake_hours_since_last_food >= 0),
        awake_hours_since_main_meal REAL NOT NULL
            CHECK(awake_hours_since_main_meal >= 0),
        recent_food_ids TEXT NOT NULL
    )""",
    """CREATE TABLE sleep_state (
        id INTEGER PRIMARY KEY REFERENCES pet_state(id) ON DELETE CASCADE CHECK(id = 1),
        kind TEXT NOT NULL CHECK(kind IN ('', 'main', 'nap', 'recovery')),
        started REAL NOT NULL CHECK(started >= 0),
        slept_seconds REAL NOT NULL CHECK(slept_seconds >= 0),
        wake_wall REAL NOT NULL CHECK(wake_wall >= 0),
        protect_until REAL NOT NULL CHECK(protect_until >= 0),
        care_break INTEGER NOT NULL CHECK(care_break IN (0, 1)),
        search_until REAL NOT NULL CHECK(search_until >= 0),
        intake_until REAL NOT NULL CHECK(intake_until >= 0),
        food_failed INTEGER NOT NULL CHECK(food_failed IN (0, 1)),
        failed_food_sources TEXT NOT NULL
    )""",
    """CREATE TABLE app_settings (
        id INTEGER PRIMARY KEY REFERENCES save_state(id) ON DELETE CASCADE
            CHECK(id = 1),
        x INTEGER, y INTEGER, scale INTEGER NOT NULL CHECK(scale IN (1, 2)),
        always_on_top INTEGER NOT NULL CHECK(always_on_top IN (0, 1)),
        auto_walk INTEGER NOT NULL CHECK(auto_walk IN (0, 1)),
        auto_routine INTEGER NOT NULL CHECK(auto_routine IN (0, 1)),
        follow_cursor INTEGER NOT NULL CHECK(follow_cursor IN (0, 1)),
        spontaneous_talk INTEGER NOT NULL CHECK(spontaneous_talk IN (0, 1)),
        observe_computer INTEGER NOT NULL CHECK(observe_computer IN (0, 1)),
        learn_rhythm INTEGER NOT NULL CHECK(learn_rhythm IN (0, 1)),
        online_social INTEGER NOT NULL CHECK(online_social IN (0, 1)),
        toolbar_x INTEGER, toolbar_y INTEGER, zodiac_sign TEXT
    )""",
)
