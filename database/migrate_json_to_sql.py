import json
import os
from pathlib import Path
from typing import Any

import aiosqlite

from bot_package.database import (
    add_bag_entry,
    add_daily_shop_state,
    add_medallium_entry,
    add_player,
    add_trophy_earned,
    add_trophy_progress,
    get_db_connection,
    init_db,
    upsert_wallet,
)

BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / "files"


async def _read_json(path: Path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def migrate_players_from_money() -> None:
    """Met à jour les joueurs depuis le fichier `files/monnaie.json` sans toucher au JSON original."""
    money_data = await _read_json(FILES_DIR / "monnaie.json")
    if not isinstance(money_data, dict):
        return

    for raw_user_id, value in money_data.items():
        if raw_user_id.endswith("_tt"):
            continue
        try:
            user_id = int(raw_user_id)
        except ValueError:
            continue

        balance = int(value)
        total_earned = int(money_data.get(f"{user_id}_tt", balance))
        await add_player(
            user_id,
            orbes_balance=balance,
            orbes_total_earned=total_earned,
        )


async def migrate_inventory_files() -> None:
    """Lit tous les fichiers JSON du médallium et les enregistre dans la table SQL."""
    inventory_dir = FILES_DIR / "inventory"
    if not inventory_dir.exists():
        return

    for file in inventory_dir.glob("*.json"):
        user_id = int(file.stem)
        await add_player(user_id)  # Crée d'abord le joueur
        inv = await _read_json(file)
        if not isinstance(inv, dict):
            continue

        for key, value in inv.items():
            if key in {"last_claim", "streak", "claim", "E", "D", "C", "B", "A", "S", "LegendaryS", "treasureS", "SpecialS", "DivinityS", "Boss", "Shiny", "Halloween", "Noël", "St-Valentin", "Printemps", "Pâques", "Estival", "Autre"}:
                continue
            if not isinstance(value, list):
                continue
            class_id = value[0] if value else "E"
            count = int(value[1]) if len(value) > 1 else 1
            await add_medallium_entry(user_id, str(key), str(class_id), count)

        # champ scalaires du médallium
        if isinstance(inv, dict):
            last_claim = inv.get("last_claim", 0)
            streak = inv.get("streak", [0, "E", 0])
            if isinstance(streak, list) and len(streak) >= 3:
                await add_player(
                    user_id,
                    last_claim=float(last_claim),
                    streak_class_id=str(streak[1]),
                    streak_count=int(streak[2]),
                )
            claim_tickets = inv.get("claim", 0)
            await add_player(user_id, claim_tickets=int(claim_tickets))


async def migrate_bag_files() -> None:
    """Lit tous les fichiers JSON du sac et les enregistre dans la table SQL."""
    bag_dir = FILES_DIR / "bag"
    if not bag_dir.exists():
        return

    for file in bag_dir.glob("*.json"):
        user_id = int(file.stem)
        await add_player(user_id)  # Crée d'abord le joueur
        bag = await _read_json(file)
        if not isinstance(bag, dict):
            continue

        for key, value in bag.items():
            if key in {"coin", "obj", "treasure", "equipped_treasure", "last_daily_reset", "amount", "daily_shop_data"}:
                continue
            if not isinstance(value, list):
                continue
            item_type = value[0] if value else "obj"
            count = int(value[1]) if len(value) > 1 else 1
            if item_type in {"coin", "obj", "treasure"}:
                await add_bag_entry(user_id, str(key), str(item_type), count)

        equipped_treasure = bag.get("equipped_treasure")
        if equipped_treasure:
            await add_player(user_id, equipped_treasure=str(equipped_treasure))

        # counters scalaires du sac
        for item_type in ("coin", "obj", "treasure"):
            total = bag.get(item_type, 0)
            if isinstance(total, int):
                await add_bag_entry(user_id, item_type, item_type, total)


async def migrate_trophy_data() -> None:
    """Détecte les données de trophées si elles existent dans les JSON de référence."""
    trophy_path = FILES_DIR / "trophe.json"
    if not trophy_path.exists():
        return
    trophy_data = await _read_json(trophy_path)
    if not isinstance(trophy_data, dict):
        return

    for user_key, value in trophy_data.items():
        try:
            user_id = int(user_key)
        except ValueError:
            continue

        await add_player(user_id)  # Crée d'abord le joueur
        if isinstance(value, dict):
            for cond, number in value.get("data", {}).items():
                await add_trophy_progress(user_id, str(cond), int(number))
            for trophy in value.get("list", []):
                await add_trophy_earned(user_id, str(trophy))


async def migrate_daily_shop_state() -> None:
    """Migration du daily shop si le JSON existe."""
    daily_shop_path = FILES_DIR / "daily_shop.json"
    if not daily_shop_path.exists():
        return
    daily_shop_data = await _read_json(daily_shop_path)
    if not isinstance(daily_shop_data, dict):
        return

    for user_key, value in daily_shop_data.items():
        try:
            user_id = int(user_key)
        except ValueError:
            continue

        await add_player(user_id)  # Crée d'abord le joueur
        if isinstance(value, list) and len(value) >= 7:
            await add_daily_shop_state(
                user_id,
                reset_at=float(value[1]),
                item_type=str(value[2]),
                item_name=str(value[5]),
                class_id=str(value[6]) if len(value) > 6 else None,
                price=int(value[3]) if len(value) > 3 else 0,
                purchased=int(value[4]) if len(value) > 4 else 0,
            )


async def _upsert_catalog_lookup(db: aiosqlite.Connection, key: str, payload: Any) -> None:
    """Insère ou met à jour un blob JSON dans la table catalog_lookup."""
    await db.execute(
        """
        INSERT INTO catalog_lookup (key_name, value_json)
        VALUES (?, ?)
        ON CONFLICT(key_name) DO UPDATE SET value_json = excluded.value_json
        """,
        (str(key), json.dumps(payload, ensure_ascii=False, separators=(",", ":"))),
    )


async def migrate_static_json_data() -> None:
    """Migrates the main static game JSON files into SQLite tables (except config and bot-data)."""
    db = await get_db_connection()
    try:
        static_catalog = {
            "yokai_list": FILES_DIR / "yokai_list.json",
            "full_name_fr": FILES_DIR / "full_name_fr.json",
            "coin": FILES_DIR / "coin.json",
            "items": FILES_DIR / "items.json",
            "tags": FILES_DIR / "tags.json",
            "monnaie": FILES_DIR / "monnaie.json",
            "terrheure_loot": FILES_DIR / "terrheure_loot.json",
            "blacklisted_yokai": FILES_DIR / "blacklisted-yokai.json",
            "shop": FILES_DIR / "shop.json",
            "daily_people": FILES_DIR / "daily.json",
            "daily_shop": FILES_DIR / "daily_shop.json",
            "fusion": FILES_DIR / "fusion.json",
            "yokai_event": FILES_DIR / "yokai_event.json",
            "yokai_event_list": FILES_DIR / "yokai_event_list.json",
            "current_event": FILES_DIR / "current_event.json",
            "trophe": FILES_DIR / "trophe.json",
            "flex": FILES_DIR / "flex.json",
            "sondage": FILES_DIR / "sondage.json",
            "exclude_match": FILES_DIR / "exclude_match.json",
            "cooldownlist": FILES_DIR / "cooldownlist.json",
        }

        for key, path in static_catalog.items():
            payload = await _read_json(path)
            if payload is not None:
                await _upsert_catalog_lookup(db, key, payload)

        shop_data = await _read_json(FILES_DIR / "shop.json")
        if isinstance(shop_data, dict):
            for page_name, page_items in shop_data.items():
                if not isinstance(page_items, dict):
                    continue
                for item_name, item_data in page_items.items():
                    if not isinstance(item_data, dict):
                        continue
                    await db.execute(
                        """
                        INSERT INTO shop_items (page_name, item_name, price, description, rang, quantity)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(page_name, item_name) DO UPDATE SET
                            price = excluded.price,
                            description = excluded.description,
                            rang = excluded.rang,
                            quantity = excluded.quantity
                        """,
                        (
                            str(page_name),
                            str(item_name),
                            int(item_data.get("price", 0)),
                            str(item_data.get("description", "")),
                            str(item_data.get("rang", "obj")),
                            int(item_data.get("quantity", 1)),
                        ),
                    )

        terrheure_data = await _read_json(FILES_DIR / "terrheure_loot.json")
        if isinstance(terrheure_data, dict):
            for key, value in terrheure_data.items():
                if key == "stats":
                    continue
                if not isinstance(value, dict):
                    continue
                await db.execute(
                    """
                    INSERT INTO terrheure_rewards (threshold, reward_type, payload)
                    VALUES (?, ?, ?)
                    ON CONFLICT(threshold) DO UPDATE SET
                        reward_type = excluded.reward_type,
                        payload = excluded.payload
                    """,
                    (int(key), str(value.get("type", "orbe")), json.dumps(value, ensure_ascii=False)),
                )

        event_data = await _read_json(FILES_DIR / "current_event.json")
        if isinstance(event_data, dict):
            for key, value in event_data.items():
                await db.execute(
                    """
                    INSERT INTO event_state (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (str(key), json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)),
                )

        trophy_data = await _read_json(FILES_DIR / "trophe.json")
        if isinstance(trophy_data, dict):
            for trophy_name, trophy_info in trophy_data.items():
                if not isinstance(trophy_info, dict):
                    continue
                await db.execute(
                    """
                    INSERT INTO trophy_catalog (trophy_name, categorie, trophy_type, condition, value, obtention, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(trophy_name) DO UPDATE SET
                        categorie = excluded.categorie,
                        trophy_type = excluded.trophy_type,
                        condition = excluded.condition,
                        value = excluded.value,
                        obtention = excluded.obtention,
                        description = excluded.description
                    """,
                    (
                        str(trophy_name),
                        str(trophy_info.get("categorie", "autre")),
                        str(trophy_info.get("type", "bronze")),
                        str(trophy_info.get("condition", "")),
                        int(trophy_info.get("value", 0)),
                        str(trophy_info.get("obtention", "")),
                        str(trophy_info.get("description", "")),
                    ),
                )

        await db.commit()
    finally:
        await db.close()


async def migrate_all_json_to_sql() -> None:
    """Migration automatique de tous les JSON connus vers SQLite sans les supprimer."""
    await init_db()
    await migrate_players_from_money()
    await migrate_inventory_files()
    await migrate_bag_files()
    await migrate_trophy_data()
    await migrate_daily_shop_state()
    await migrate_static_json_data()
