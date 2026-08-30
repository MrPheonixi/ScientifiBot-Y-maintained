-- ============================================================
-- ScientifiBot-Y — schéma SQLite (medallium + bag + wallet)
-- ============================================================
-- Rôle : remplacer les fichiers JSON des inventaires / sacs / monnaie.
-- On garde la structure de ton schéma, avec quelques garde-fous SQLite.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS players (
    user_id             INTEGER PRIMARY KEY,
    last_claim          REAL    NOT NULL DEFAULT 0,
    claim_tickets       INTEGER NOT NULL DEFAULT 0 CHECK (claim_tickets >= 0),
    streak_class_id     TEXT,
    streak_count        INTEGER NOT NULL DEFAULT 0 CHECK (streak_count >= 0),
    equipped_treasure   TEXT,
    orbes_balance       INTEGER NOT NULL DEFAULT 0,
    orbes_total_earned  INTEGER NOT NULL DEFAULT 0,
    first_seen_at       INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE IF NOT EXISTS medallium_yokai (
    user_id     INTEGER NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
    yokai_name  TEXT    NOT NULL,
    class_id    TEXT    NOT NULL,
    count       INTEGER NOT NULL DEFAULT 1 CHECK (count >= 1),
    PRIMARY KEY (user_id, yokai_name)
);

CREATE INDEX IF NOT EXISTS idx_medallium_yokai_name ON medallium_yokai(yokai_name);

CREATE TABLE IF NOT EXISTS bag_items (
    user_id     INTEGER NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
    item_name   TEXT    NOT NULL,
    item_type   TEXT    NOT NULL CHECK (item_type IN ('coin', 'obj', 'treasure')),
    count       INTEGER NOT NULL DEFAULT 1 CHECK (count >= 1),
    PRIMARY KEY (user_id, item_name)
);

CREATE INDEX IF NOT EXISTS idx_bag_items_name ON bag_items(item_name);

CREATE TABLE IF NOT EXISTS trophy_progress (
    user_id          INTEGER NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
    trophy_condition TEXT    NOT NULL,
    value            INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, trophy_condition)
);

CREATE TABLE IF NOT EXISTS trophy_earned (
    user_id     INTEGER NOT NULL REFERENCES players(user_id) ON DELETE CASCADE,
    trophy_name TEXT    NOT NULL,
    earned_at   INTEGER NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, trophy_name)
);

CREATE TABLE IF NOT EXISTS daily_shop_state (
    user_id     INTEGER PRIMARY KEY REFERENCES players(user_id) ON DELETE CASCADE,
    reset_at    REAL    NOT NULL,
    item_type   TEXT    NOT NULL CHECK (item_type IN ('coin', 'object', 'yokai')),
    item_name   TEXT    NOT NULL,
    class_id    TEXT,
    price       INTEGER NOT NULL,
    purchased   INTEGER NOT NULL DEFAULT 0 CHECK (purchased IN (0, 1))
);

-- ============================================================
-- Données de jeu globales (hors configuration et données bot-data)
-- ============================================================
CREATE TABLE IF NOT EXISTS shop_items (
    page_name   TEXT NOT NULL,
    item_name   TEXT NOT NULL,
    price       INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT '',
    rang        TEXT DEFAULT 'obj',
    quantity    INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (page_name, item_name)
);

CREATE TABLE IF NOT EXISTS terrheure_rewards (
    threshold   INTEGER PRIMARY KEY,
    reward_type TEXT NOT NULL,
    payload     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_state (
    key         TEXT PRIMARY KEY,
    value       TEXT
);

CREATE TABLE IF NOT EXISTS trophy_catalog (
    trophy_name TEXT PRIMARY KEY,
    categorie   TEXT NOT NULL,
    trophy_type TEXT NOT NULL,
    condition   TEXT NOT NULL,
    value       INTEGER NOT NULL DEFAULT 0,
    obtention   TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_yokai (
    class_id    TEXT NOT NULL,
    yokai_name  TEXT NOT NULL,
    payload     TEXT NOT NULL,
    PRIMARY KEY (class_id, yokai_name)
);

CREATE TABLE IF NOT EXISTS catalog_items (
    item_name   TEXT PRIMARY KEY,
    payload     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_coins (
    coin_name   TEXT PRIMARY KEY,
    payload     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_tags (
    tag_name    TEXT PRIMARY KEY,
    payload     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_events (
    event_name  TEXT PRIMARY KEY,
    payload     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_daily_shop (
    key_name    TEXT PRIMARY KEY,
    value_json  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_lookup (
    key_name    TEXT PRIMARY KEY,
    value_json  TEXT NOT NULL
);
