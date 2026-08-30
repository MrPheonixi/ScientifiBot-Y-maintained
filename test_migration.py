import asyncio
from bot_package.database import get_all_player_ids, get_wallet_sql, get_inv_sql

async def test():
    ids = await get_all_player_ids()
    print(f'Total players in DB: {len(ids)}')
    for uid in ids[:3]:
        wallet = await get_wallet_sql(uid)
        inv = await get_inv_sql(uid)
        yokai_count = len([k for k in inv.keys() if k not in {
            "last_claim", "streak", "claim", "E", "D", "C", "B", "A", "S",
            "LegendaryS", "treasureS", "SpecialS", "DivinityS", "Boss", "Shiny"
        }])
        print(f'Player {uid}: wallet={wallet["balance"]}orbes, {yokai_count} yokais')

asyncio.run(test())
