import json
import os
from pathlib import Path
from typing import Any

import aiosqlite

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "scientibot.db")))
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


async def get_db_connection() -> aiosqlite.Connection:
    """Crée une connexion SQLite asynchrone avec les contraintes FK activées."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON;")
    return db


async def init_db() -> Path:
    """Initialise la base SQLite en exécutant le schéma SQL."""
    db = await get_db_connection()
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        await db.executescript(schema_sql)
        await db.commit()
    finally:
        await db.close()
    return DB_PATH


async def add_player(
    user_id: int,
    *,
    last_claim: float | None = None,
    claim_tickets: int | None = None,
    streak_class_id: str | None = None,
    streak_count: int | None = None,
    equipped_treasure: str | None = None,
    orbes_balance: int | None = None,
    orbes_total_earned: int | None = None,
    db: aiosqlite.Connection | None = None,
) -> None:
    """Crée ou met à jour le joueur dans la table `players`."""
    owns_db = db is None
    db_conn = db or await get_db_connection()
    try:
        await db_conn.execute(
            """
            INSERT INTO players (
                user_id, last_claim, claim_tickets, streak_class_id, streak_count,
                equipped_treasure, orbes_balance, orbes_total_earned
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                last_claim = COALESCE(excluded.last_claim, players.last_claim),
                claim_tickets = COALESCE(excluded.claim_tickets, players.claim_tickets),
                streak_class_id = COALESCE(excluded.streak_class_id, players.streak_class_id),
                streak_count = COALESCE(excluded.streak_count, players.streak_count),
                equipped_treasure = COALESCE(excluded.equipped_treasure, players.equipped_treasure),
                orbes_balance = COALESCE(excluded.orbes_balance, players.orbes_balance),
                orbes_total_earned = COALESCE(excluded.orbes_total_earned, players.orbes_total_earned)
            """,
            (
                user_id,
                last_claim if last_claim is not None else 0,
                claim_tickets if claim_tickets is not None else 0,
                streak_class_id,
                streak_count if streak_count is not None else 0,
                equipped_treasure,
                orbes_balance if orbes_balance is not None else 0,
                orbes_total_earned if orbes_total_earned is not None else 0,
            ),
        )
        if owns_db:
            await db_conn.commit()
    finally:
        if owns_db:
            await db_conn.close()


async def add_medallium_entry(
    user_id: int,
    yokai_name: str,
    class_id: str,
    count: int = 1,
    db: aiosqlite.Connection | None = None,
) -> None:
    """Ajoute ou met à jour un Yo-kai dans le médallium SQL."""
    owns_db = db is None
    db_conn = db or await get_db_connection()
    try:
        await db_conn.execute(
            """
            INSERT INTO medallium_yokai (user_id, yokai_name, class_id, count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, yokai_name) DO UPDATE SET
                class_id = excluded.class_id,
                count = excluded.count
            """,
            (user_id, yokai_name, class_id, max(1, int(count))),
        )
        if owns_db:
            await db_conn.commit()
    finally:
        if owns_db:
            await db_conn.close()


async def add_bag_entry(
    user_id: int,
    item_name: str,
    item_type: str,
    count: int = 1,
    db: aiosqlite.Connection | None = None,
) -> None:
    """Ajoute ou met à jour un objet dans le sac SQL."""
    if item_type not in {"coin", "obj", "treasure"}:
        raise ValueError(f"Type d'item invalide pour le sac : {item_type!r}")

    owns_db = db is None
    db_conn = db or await get_db_connection()
    try:
        await db_conn.execute(
            """
            INSERT INTO bag_items (user_id, item_name, item_type, count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, item_name) DO UPDATE SET
                item_type = excluded.item_type,
                count = excluded.count
            """,
            (user_id, item_name, item_type, max(1, int(count))),
        )
        if owns_db:
            await db_conn.commit()
    finally:
        if owns_db:
            await db_conn.close()


async def add_trophy_progress(user_id: int, trophy_condition: str, value: int = 0, db: aiosqlite.Connection | None = None) -> None:
    """Met à jour la progression d'un trophée."""
    owns_db = db is None
    db_conn = db or await get_db_connection()
    try:
        await db_conn.execute(
            """
            INSERT INTO trophy_progress (user_id, trophy_condition, value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, trophy_condition) DO UPDATE SET
                value = excluded.value
            """,
            (user_id, trophy_condition, int(value)),
        )
        if owns_db:
            await db_conn.commit()
    finally:
        if owns_db:
            await db_conn.close()


async def add_trophy_earned(user_id: int, trophy_name: str, db: aiosqlite.Connection | None = None) -> None:
    """Marque un trophée obtenu."""
    owns_db = db is None
    db_conn = db or await get_db_connection()
    try:
        await db_conn.execute(
            """
            INSERT OR IGNORE INTO trophy_earned (user_id, trophy_name)
            VALUES (?, ?)
            """,
            (user_id, trophy_name),
        )
        if owns_db:
            await db_conn.commit()
    finally:
        if owns_db:
            await db_conn.close()


async def add_daily_shop_state(
    user_id: int,
    *,
    reset_at: float,
    item_type: str,
    item_name: str,
    class_id: str | None,
    price: int,
    purchased: int = 0,
    db: aiosqlite.Connection | None = None,
) -> None:
    """Insert ou met à jour l'état du shop quotidien."""
    owns_db = db is None
    db_conn = db or await get_db_connection()
    try:
        await db_conn.execute(
            """
            INSERT INTO daily_shop_state (
                user_id, reset_at, item_type, item_name, class_id, price, purchased
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                reset_at = excluded.reset_at,
                item_type = excluded.item_type,
                item_name = excluded.item_name,
                class_id = excluded.class_id,
                price = excluded.price,
                purchased = excluded.purchased
            """,
            (user_id, float(reset_at), item_type, item_name, class_id, int(price), int(purchased)),
        )
        if owns_db:
            await db_conn.commit()
    finally:
        if owns_db:
            await db_conn.close()


async def upsert_wallet(user_id: int, orbes_balance: int, orbes_total_earned: int) -> None:
    """Met à jour le solde et le total gagné du joueur."""
    await add_player(
        user_id,
        orbes_balance=orbes_balance,
        orbes_total_earned=orbes_total_earned,
    )


async def get_wallet_sql(user_id: int) -> dict:
    """Lit le wallet du joueur depuis SQLite."""
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT orbes_balance, orbes_total_earned FROM players WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return {"balance": 0, "total_earned": 0}
        return {"balance": int(row[0]), "total_earned": int(row[1])}
    finally:
        await db.close()


async def get_inv_sql(user_id: int) -> dict:
    """Retourne le médallium au format JSON-compatible pour les fonctions du bot."""
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT last_claim, claim_tickets, streak_class_id, streak_count FROM players WHERE user_id = ?",
            (user_id,),
        )
        player = await cursor.fetchone()

        cursor = await db.execute(
            "SELECT yokai_name, class_id, count FROM medallium_yokai WHERE user_id = ? ORDER BY yokai_name",
            (user_id,),
        )
        rows = await cursor.fetchall()

        inventory = {
            "last_claim": float(player[0]) if player and player[0] is not None else 0,
            "streak": [0, player[2] or "E", int(player[3]) if player and player[3] is not None else 0],
            "claim": int(player[1]) if player and player[1] is not None else 0,
        }

        class_totals = {"E": 0, "D": 0, "C": 0, "B": 0, "A": 0, "S": 0, "LegendaryS": 0, "treasureS": 0, "SpecialS": 0, "DivinityS": 0, "Boss": 0, "Shiny": 0}
        for row in rows:
            key = row[0]
            item_class = row[1]
            count = int(row[2])
            inventory[key] = [item_class, count]
            if item_class in class_totals:
                class_totals[item_class] += count

        for class_id, total in class_totals.items():
            inventory[class_id] = total

        return inventory
    finally:
        await db.close()


async def get_bag_sql(user_id: int) -> dict:
    """Retourne la sacoche au format JSON-compatible pour le bot."""
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT equipped_treasure FROM players WHERE user_id = ?",
            (user_id,),
        )
        player = await cursor.fetchone()

        cursor = await db.execute(
            "SELECT item_name, item_type, count FROM bag_items WHERE user_id = ? ORDER BY item_name",
            (user_id,),
        )
        rows = await cursor.fetchall()

        bag = {
            "coin": 0,
            "obj": 0,
            "treasure": 0,
            "equipped_treasure": player[0] if player and player[0] is not None else None,
        }

        for row in rows:
            name = row[0]
            item_type = row[1]
            count = int(row[2])
            bag[name] = [item_type, count]
            if item_type in bag:
                bag[item_type] += count

        return bag
    finally:
        await db.close()


async def save_inv_sql(user_id: int, payload: dict) -> None:
    """Écrit un médallium complet dans SQLite et garde un backup JSON."""
    await init_db()
    db = await get_db_connection()
    try:
        await db.execute("DELETE FROM medallium_yokai WHERE user_id = ?", (user_id,))

        last_claim = payload.get("last_claim", 0)
        streak = payload.get("streak", [0, "E", 0])
        claim = payload.get("claim", 0)

        await add_player(
            user_id,
            last_claim=float(last_claim),
            claim_tickets=int(claim),
            streak_class_id=str(streak[1]) if isinstance(streak, list) and len(streak) > 1 else None,
            streak_count=int(streak[2]) if isinstance(streak, list) and len(streak) > 2 else 0,
            db=db,
        )

        for key, value in payload.items():
            if key in {"last_claim", "streak", "claim", "E", "D", "C", "B", "A", "S", "LegendaryS", "treasureS", "SpecialS", "DivinityS", "Boss", "Shiny", "Halloween", "Noël", "St-Valentin", "Printemps", "Pâques", "Estival", "Autre"}:
                continue
            if not isinstance(value, list) or not value:
                continue
            class_id = value[0]
            count = int(value[1]) if len(value) > 1 else 1
            await add_medallium_entry(user_id, str(key), str(class_id), count, db=db)

        await db.commit()
    finally:
        await db.close()

    json_path = BASE_DIR / "files" / "inventory" / f"{user_id}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


async def save_bag_sql(user_id: int, payload: dict) -> None:
    """Écrit une sacoche complète dans SQLite et garde un backup JSON."""
    await init_db()
    db = await get_db_connection()
    try:
        await db.execute("DELETE FROM bag_items WHERE user_id = ?", (user_id,))
        for key, value in payload.items():
            if key in {"coin", "obj", "treasure", "equipped_treasure", "last_daily_reset", "amount", "daily_shop_data"}:
                continue
            if not isinstance(value, list) or not value:
                continue
            item_type = value[0]
            count = int(value[1]) if len(value) > 1 else 1
            if item_type in {"coin", "obj", "treasure"}:
                await add_bag_entry(user_id, str(key), str(item_type), count, db=db)

        await add_player(user_id, equipped_treasure=payload.get("equipped_treasure"), db=db)
        await db.commit()
    finally:
        await db.close()

    json_path = BASE_DIR / "files" / "bag" / f"{user_id}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


async def _read_json_file(path: str | os.PathLike[str]) -> Any:
    """Lit un JSON en gardant les fichiers JSON d'origine intacts."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def get_all_player_ids() -> list[int]:
    """Récupère la liste de tous les IDs de joueurs depuis la DB."""
    db = await get_db_connection()
    try:
        cursor = await db.execute("SELECT user_id FROM players ORDER BY user_id")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        await db.close()

