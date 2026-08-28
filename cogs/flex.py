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
        brute_inventory = await cf.get_inv(ctx.author.id)

        total = 0
        actual = 0

        for class_id in data.class_list:
            total += data.list_len[class_id]
            actual += brute_inventory.get(class_id, 0)

        completion = round((actual / total) * 100, 2) if total else 0

        #calculate the total of unique yokai owned by the user
        unique_yokai = len(brute_inventory.keys())-14
        flex_embed.add_field(name="Statistiques relatif au Médallium", 
                             value=f"""complété à *{completion}% {actual}/{total}* 
                            total de yokai possédés: {actual}
                            yokai uniques possédés: {unique_yokai}""", inline=False)
        u_yokai = []
        u_items = []
        flex_embed.add_field(name="yokai et item spéciaux", value=f"yokai :{u_yokai} \n items :{u_items}", inline=False)

async def setup(bot):
    await bot.add_cog(flex(bot))