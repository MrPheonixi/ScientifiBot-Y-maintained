import bot_package.data as data
import discord
from discord.ext import commands
import bot_package.Custom_func as cf


def _normalize_yokai_name(name: str) -> str:
    try:
        return name.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


class flex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="flex")
    async def flex(self, ctx: commands.Context):
        #start the embed creation
        flex_embed = discord.Embed(title="Voici vos statistiques de collection :"
                                   , color=discord.Color.blue())
        # calculate all the needed information to display the flex message
        # calculate the percentage of the medallium completed
        inv = await cf.get_inv(ctx.author.id)

        yokai_names = {
            _normalize_yokai_name(yokai)
            for yokai_data in (*data.yokai_data.values(), *data.yokai_event_data.values())
            for yokai in yokai_data["yokai_list"]
        }
        tag_names = {
            _normalize_yokai_name(yokai)
            for tag in data.TAGS_DATA.values()
            for yokai in tag.get("list", [])
        }
        tracked_names = yokai_names | tag_names
        inventory_counts = {}
        for yokai, details in inv.items():
            normalized_yokai = _normalize_yokai_name(yokai)
            if normalized_yokai not in tracked_names:
                continue
            if not isinstance(details, list) or not details or not isinstance(details[0], str):
                continue
            copies = details[1] if len(details) > 1 and isinstance(details[1], int) else 1
            inventory_counts[normalized_yokai] = copies

        unique_yokai = len(yokai_names.intersection(inventory_counts))
        total = len(yokai_names)
        actual = sum(inventory_counts[yokai] for yokai in yokai_names if yokai in inventory_counts)
        completion = round((unique_yokai / total) * 100, 2) if total else 0
        
        flex_embed.add_field(name="Statistiques relatif au Médallium", 
                             value=f"""complété à *{completion}% {unique_yokai}/{total}* 
                            total de yokai possédés: {actual}""", inline=False)
        
        
        
        
        completed_tags = []
        tags = data.TAGS_DATA
        for tag_n, tag in tags.items():
            tag_yokai = {_normalize_yokai_name(yokai) for yokai in tag.get("list", [])}
            copies = [inventory_counts.get(yokai, 0) for yokai in tag_yokai]
            if copies and all(count > 0 for count in copies):
                completed_tags.append(f"{tag_n} (x{min(copies)})")






        if completed_tags:
            flex_embed.add_field(name="Tags complétés", value=", ".join(completed_tags), inline=False)
        else:
            flex_embed.add_field(name="Tags complétés", value="Aucun tag complété pour le moment.", inline=False)
        u_yokai = []
        u_items = []
        u_yokai_poss = []
        u_items_poss = []
        bag = await cf.get_bag(ctx.author.id)
        for yk in u_yokai:
            if yk in inv:
                u_yokai_poss.append(yk)
        for item in u_items:
            if item in bag:
                u_items_poss.append(item)

        special_lines = []
        if u_yokai:
            special_lines.append(f"Yokai spéciaux : {', '.join(u_yokai_poss)}")
        if u_items:
            special_lines.append(f"Items spéciaux : {', '.join(u_items_poss)}")

        if special_lines:
            flex_embed.add_field(name="Yokai et items spéciaux", value="\n".join(special_lines), inline=False)

        await ctx.send(embed=flex_embed)

async def setup(bot):
    await bot.add_cog(flex(bot))