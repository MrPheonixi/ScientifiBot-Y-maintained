# Migration JSON -> SQLite

## Étape 1 — tables SQL

Les tables sont créées par [database/schema.sql](database/schema.sql).

Les objets migrés sont :
- les joueurs : `players`
- les Yo-kai du médallium : `medallium_yokai`
- les objets du sac : `bag_items`
- la progression trophée : `trophy_progress` / `trophy_earned`
- le shop quotidien : `daily_shop_state`

## Étape 2 — initialiser la base

Utiliser le helper Python dans [bot_package/database.py](../bot_package/database.py).

```python
import asyncio
from bot_package.database import init_db

async def main():
    await init_db()
    print("DB OK")

asyncio.run(main())
```

## Étape 3 — migration des données JSON existantes

Pour chaque fichier JSON existant :
1. lire les données JSON actuelles
2. convertir chaque structure en insertion SQL
3. remplir `players` avec les utilisateurs connus
4. migrer le médallium : `files/inventory/{id}.json`
5. migrer le sac : `files/bag/{id}.json`
6. migrer la monnaie : `files/monnaie.json`
7. migrer les données de shop / trophées / daily

## Étape 4 — remplacer les accès JSON par SQL

A la fin, il faudra remplacer les fonctions comme :
- `Cf.get_inv()`
- `Cf.get_bag()`
- `economy.add()/remove()/get_balance()`

par des fonctions qui lisent/écrivent dans SQLite.

## Étape 5 — validation

Vérifier que :
- un joueur ne peut pas avoir un médallium vide à l'insertion
- les `CHECK` SQLite sont respectés
- les clés étrangères ne cassent pas la base
- les commandes Discord continuent de fonctionner avec les mêmes données

## Point de vigilance

J'ai conservé la structure du schéma donné, sans modification de logique métier. Le code SQL est prêt pour la prochaine étape de migration des call sites.
