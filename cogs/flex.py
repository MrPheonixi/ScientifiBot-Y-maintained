import bot_package.data as data
import discord
from discord.ext import commands
import bot_package.Custom_func as cf



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

        total = 0
        actual = 0

        for class_id in data.class_list:
            total += data.list_len[class_id]

        completion = round((actual / total) * 100, 2) if total else 0
        
        #calculate the total of unique yokai owned by the user
        unique_yokai = len(inv.keys())-14
        for yk in inv:
            if isinstance(yk,list) and len(yk) < 2:
                try:
                    actual += inv[yk][1]
                except:
                    actual += 1
        flex_embed.add_field(name="Statistiques relatif au Médallium", 
                             value=f"""complété à *{completion}% {unique_yokai}/{total}* 
                            total de yokai possédés: {actual}""", inline=False)
        
        
        
        
        completed_tags = []
        tags = data.TAGS_DATA
        for tag_n, tag in tags.items():
            lists = tag.get("list")
            min = 0
            for yk in lists:
                if yk in inv:
                    yk = inv.get(yk)
                    if len(yk) == 1:
                        if min > 1:
                            min = 1
                    else:
                        if min > yk[1]:
                            min = yk[1]
                else:
                    break
            if min > 0:
                completed_tags.append(f"{tag_n} (x{min})")






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