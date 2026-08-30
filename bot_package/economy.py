import json
import bot_package.data as data
import bot_package.Custom_func as Cf
from bot_package.database import get_wallet_sql, upsert_wallet


async def create_user_info(user_id: int) -> None:
    from bot_package.database import get_db_connection

    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT orbes_balance, orbes_total_earned FROM players WHERE user_id = ?",
            (user_id,),
        )
        player_row = await cursor.fetchone()
    finally:
        await db.close()

    if player_row is not None:
        data.MONEY_DATA[str(user_id)] = int(player_row[0])
        data.MONEY_DATA[f"{user_id}_tt"] = int(player_row[1])
        data.save_json("./files/monnaie.json", data.MONEY_DATA)
        return

    try:
        wallet = await get_wallet_sql(user_id)
        if wallet["balance"] == 0 and wallet["total_earned"] == 0:
            data.MONEY_DATA[str(user_id)] = 0
            if not str(user_id) in data.MONEY_DATA.keys():
                data.MONEY_DATA[str(user_id)] = 0
            user_inventory = await Cf.get_inv(user_id)
            for nom, info in user_inventory.items():
                if isinstance(info, list) and len(info) <= 2 and len(info) > 1:
                    point = data.class_to_point[info[0]]
                    bonus_copies = int(info[1]) - 1
                    data.MONEY_DATA[str(user_id)] += point * bonus_copies
            data.save_json("./files/monnaie.json", data.MONEY_DATA)
            await upsert_wallet(user_id, int(data.MONEY_DATA[str(user_id)]), int(data.MONEY_DATA.get(f"{user_id}_tt", data.MONEY_DATA[str(user_id)])))
    except Exception:
        pass

    if not str(user_id) in data.MONEY_DATA.keys():
        data.MONEY_DATA[str(user_id)] = 0
    if not f"{user_id}_tt" in data.MONEY_DATA.keys():
        data.MONEY_DATA[f"{user_id}_tt"] = data.MONEY_DATA[str(user_id)]
        data.save_json("./files/monnaie.json", data.MONEY_DATA)


async def add(user_id: int, amount: int) -> None:
    await create_user_info(user_id)
    current_balance = int(data.MONEY_DATA.get(str(user_id), await get_balance(user_id)))
    current_total = int(data.MONEY_DATA.get(f"{user_id}_tt", current_balance))
    data.MONEY_DATA[str(user_id)] = current_balance + amount
    if amount > 0:
        data.MONEY_DATA[f"{user_id}_tt"] = current_total + amount
    else:
        data.MONEY_DATA[f"{user_id}_tt"] = current_total
    await upsert_wallet(user_id, int(data.MONEY_DATA[str(user_id)]), int(data.MONEY_DATA[f"{user_id}_tt"]))
    data.save_json("./files/monnaie.json", data.MONEY_DATA)


async def get_balance(user_id: int) -> int:
    await create_user_info(user_id)
    try:
        wallet = await get_wallet_sql(user_id)
        # SQLite est la source de vérité. Un solde à 0 est un vrai solde,
        # il ne faut pas retomber sur le JSON de secours dans ce cas.
        return int(wallet["balance"])
    except Exception:
        pass
    return int(data.MONEY_DATA.get(str(user_id), 0))


async def reset(user_id: int, tt: bool = False) -> None:
    data.MONEY_DATA[str(user_id)] = 0
    if tt:
        data.MONEY_DATA[f"{user_id}_tt"] = 0
    await upsert_wallet(user_id, 0, 0 if tt else int(data.MONEY_DATA.get(f"{user_id}_tt", 0)))
    data.save_json("./files/monnaie.json", data.MONEY_DATA)


async def del_info(user_id: int) -> None:
    if str(user_id) in data.MONEY_DATA.keys():
        del data.MONEY_DATA[str(user_id)]
    if f"{user_id}_tt" in data.MONEY_DATA.keys():
        del data.MONEY_DATA[f"{user_id}_tt"]
    data.save_json("./files/monnaie.json", data.MONEY_DATA)


async def add_rank_orbe(user_id: int, rank) -> None:
    await create_user_info(user_id)
    p = data.class_to_point[rank]
    data.MONEY_DATA[str(user_id)] += p
    data.MONEY_DATA[f"{user_id}_tt"] += p
    await upsert_wallet(user_id, int(data.MONEY_DATA[str(user_id)]), int(data.MONEY_DATA[f"{user_id}_tt"]))
    data.save_json("./files/monnaie.json", data.MONEY_DATA)
    await Cf.update_trophe_data(user_id, "orbes", p, "add")
