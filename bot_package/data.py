import os
import asyncio
import json
import sqlite3
from pathlib import Path


"""
This module provide the data imported for various json in a python usable format.

Also some assets like default inv or bag.
"""

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "scientibot.db")))


#func to fix a bug, on windows only ofc ;)
if os.name == "nt":  # Only execute on Windows
    def fix_encoding(obj):
        #the func that encode well everything; bcs we are french, we use é, à, è
            if isinstance(obj, dict):
                return {fix_encoding(k): fix_encoding(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [fix_encoding(item) for item in obj]
            elif isinstance(obj, str):
                try:
                    return obj.encode('latin-1').decode('utf-8')
                except UnicodeEncodeError:
                    return obj
                except UnicodeDecodeError:
                    return obj
            else:
                return obj

else:
    def fix_encoding(obj):
        return obj


# Function to open JSON data
def open_json(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return fix_encoding(json.load(f))
    return {}


# Function to save JSON data
def save_json(file_path: str, data: dict, ):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _catalog_key_from_path(file_path: str) -> str | None:
    normalized = str(file_path).replace('\\', '/').strip()
    if normalized.startswith('./'):
        normalized = normalized[2:]
    if normalized.startswith('/'):
        normalized = normalized.lstrip('/')
    if normalized.startswith('files/'):
        normalized = normalized[len('files/') :]
    if not normalized:
        return None
    name = Path(normalized).stem
    if name == 'blacklisted-yokai':
        return 'blacklisted_yokai'
    if name == 'bot-data':
        return None
    if name == 'configuration':
        return None
    return name


def _read_sql_catalog_json(key_name: str, default=None):
    if not DB_PATH.exists():
        return default
    try:
        with sqlite3.connect(DB_PATH) as connection:
            row = connection.execute(
                "SELECT value_json FROM catalog_lookup WHERE key_name = ?",
                (key_name,),
            ).fetchone()
    except sqlite3.Error:
        return default
    if row is None:
        return default
    try:
        return fix_encoding(json.loads(row[0]))
    except (TypeError, ValueError):
        return default


def _load_yokai_lengths(yokai_data):
    if not isinstance(yokai_data, dict):
        return {}
    return {
        "E": len(yokai_data.get("E", {}).get("yokai_list", [])),
        "D": len(yokai_data.get("D", {}).get("yokai_list", [])),
        "C": len(yokai_data.get("C", {}).get("yokai_list", [])),
        "B": len(yokai_data.get("B", {}).get("yokai_list", [])),
        "A": len(yokai_data.get("A", {}).get("yokai_list", [])),
        "S": len(yokai_data.get("S", {}).get("yokai_list", [])),
        "LegendaryS": len(yokai_data.get("LegendaryS", {}).get("yokai_list", [])),
        "treasureS": len(yokai_data.get("treasureS", {}).get("yokai_list", [])),
        "DivinityS": len(yokai_data.get("DivinityS", {}).get("yokai_list", [])),
        "SpecialS": len(yokai_data.get("SpecialS", {}).get("yokai_list", [])),
        "Boss": len(yokai_data.get("Boss", {}).get("yokai_list", [])),
        "Shiny": len(yokai_data.get("Shiny", {}).get("yokai_list", [])),
    }


#Get Yo-kai lists from SQLite only, except configuration and bot-data that remain JSON.
yokai_data = _read_sql_catalog_json("yokai_list", {})
list_len = _load_yokai_lengths(yokai_data)

#Make the class list and the proba
class_list = ['E', 'D', 'C', 'B', 'A', 'S', 'LegendaryS', "treasureS", "SpecialS", 'DivinityS', "Boss", "Shiny"]
proba_list = [0.4165, 0.2, 0.12, 0.12, 0.08, 0.04, 0.0075, 0.0075, 0.0075, 0.005, 0.0025, 0.0010]
#                E     D     C     B     A     S      L       t       Sp      D       B      Sh
golden_proba_list = [0.0, 0.0, 0.0, 0.3, 0.25, 0.2, 0.10, 0.10, 0.005, 0.025, 0.01, 0.01]

yokai_list_full = _read_sql_catalog_json("full_name_fr", {})

# get image and emoji list from bot-data.json only
with open("./files/bot-data.json", "r", encoding="utf-8") as bot_data_file:
    bot_data = fix_encoding(json.load(bot_data_file))
    image_link = {}
    for link in bot_data.get("image_link", {}):
        image_link[link] = bot_data["image_link"][link]

    emoji = {}
    for emojis in bot_data.get("emoji", {}):
        emoji[emojis] = bot_data["emoji"][emojis]

# Get configuration.json only
with open("./configuration.json", "r", encoding="utf-8") as config:
    config_data = fix_encoding(json.load(config))
    team_member_id = config_data.get("team_members_id", [])
    team_bypass_cooldown = config_data.get("team_bypass_cooldown", False)

#Get all coin related stuff (a lot)
coin_data = _read_sql_catalog_json("coin", {})
coin_list = list(coin_data.keys())
coin_proba = [coin_data[coin].get("proba", 0) for coin in coin_list]

coin_loot = {}
for dirpath, dirnames, filenames in os.walk("./files/coin"):
    for file in filenames:
        if not file.endswith(".json"):
            continue
        coin_loot_brute = open_json(f"./files/coin/{file}")
        coin_key = file.removesuffix(".json")
        coin_loot[coin_key] = {"list": coin_loot_brute.get("list", {})}
        proba_in_order = []
        element_in_order = []
        for element in coin_loot[coin_key]["list"]:
            element_in_order.append(element)
            proba_in_order.append(coin_loot[coin_key]["list"][element][1])
        coin_loot[coin_key]["proba_in_order"] = proba_in_order
        coin_loot[coin_key]["element_in_order"] = element_in_order

#items info
item = _read_sql_catalog_json("items", {})

#tag info
TAGS_DATA = _read_sql_catalog_json("tags", {})

#Sort tags data
for value in TAGS_DATA.values():
    if isinstance(value, dict) and isinstance(value.get("list"), list):
        value["list"].sort()

#money info
MONEY_DATA = _read_sql_catalog_json("monnaie", {})

#terheure loot info
terrheure = _read_sql_catalog_json("terrheure_loot", {})

#blacklist info for normal bkai
blacklist = _read_sql_catalog_json("blacklisted_yokai", {})

#items info for shop
shop_item = _read_sql_catalog_json("shop", {})

#list of people who use daily command today
daily_people = _read_sql_catalog_json("daily_people", {"people": []})

#information about the daily shop
daily_shop = _read_sql_catalog_json("daily_shop", {})

fusion = _read_sql_catalog_json("fusion", {})

yokai_event_list = _read_sql_catalog_json("yokai_event_list", {})
yokai_event_data = _read_sql_catalog_json("yokai_event", {})
event_list_len = {
    "Halloween": len(yokai_event_data.get("Halloween", {}).get("yokai_list", [])),
    "Noël": len(yokai_event_data.get("Noël", {}).get("yokai_list", [])),
    "St-Valentin": len(yokai_event_data.get("St-Valentin", {}).get("yokai_list", [])),
    "Printemps": len(yokai_event_data.get("Printemps", {}).get("yokai_list", [])),
    "Pâques": len(yokai_event_data.get("Pâques", {}).get("yokai_list", [])),
    "Estival": len(yokai_event_data.get("Estival", {}).get("yokai_list", [])),
    "Autre": len(yokai_event_data.get("Autre", {}).get("yokai_list", [])),
}

current_event_data = _read_sql_catalog_json("current_event", {})
current_event = current_event_data.get("current_event") if isinstance(current_event_data, dict) else None

if current_event is not None:
    current_event_payload = yokai_event_data.get(current_event, {})
    if isinstance(current_event_payload, dict):
        list_len["SpecialS"] = max(0, list_len.get("SpecialS", 0) - len(current_event_payload.get("yokai_list", [])))

trophe_data = _read_sql_catalog_json("trophe", {})

trophe_color = {
    "bronze": "#4e3609",
    "argent": "#5d5f5d",
    "or": "#fffb00"
}
#information about the flex command
flex = _read_sql_catalog_json("flex", {})

#yokai sondage info
sondage = _read_sql_catalog_json("sondage", {})

default_medallium  = {
                        "last_claim" : 10000,
                        "streak": [
                            0, # Magic value, is never used or modified
                            "E",
                            0
                        ],
                        "E" : 0,
                        "D" : 0,
                        "C" : 0,
                        "B" : 0,
                        "A" : 0,
                        "S" : 0,
                        "LegendaryS" : 0,
                        "treasureS" : 0,
                        "SpecialS" : 0,
                        "DivinityS" : 0,
                        "Boss" : 0,
                        "Shiny" : 0,
                        "Halloween" : 0,
                        "Noël" : 0,
                        "St-Valentin" : 0,
                        "Printemps" : 0,
                        "Pâques" : 0,
                        "Estival" : 0,
                        "Autre" : 0
                    }

default_bag = {
                    "coin" : 0,
                    "obj" : 0,
                    "treasure" : 0,
                }


#The class to point dict

class_to_point = {
    "E" : 1,
    "D" : 2,
    "C" : 4,
    "B" : 4,
    "A" : 8,
    "S" : 16,
    "LegendaryS" : 24,
    "treasureS" : 24,
    "SpecialS" : 24,
    "DivinityS" : 32,
    "Boss" : 64,
    "Shiny" : 82,
}
