import discord
from discord.ext import commands
import bot_package.data as data
import bot_package.economy as eco


ecof = data.MONEY_DATA


class economy(commands.Cog):
    """
    New ✨! 
    Contient toutes les opérations liées au Orbes.
    
    Vous obtenez des orbes lorsque vous obtenez un Yo-kai en double au bingo-kai,
    la valeur d'orbe que vous obtenez correspond à la valeur en points (voir `/stats`) du rang.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="orbe")
    async def orbe(self, ctx, user: discord.Member = None):
        """
        Affiche votre solde d'orbe oni, ou celui de l'utilisateur spécifié.
        """
        if not user == None and not str(user.id) in data.MONEY_DATA.keys():
            return await ctx.send("Cet utilisateur n'a pas encore gagné d'orbes oni.")
        else:
            if user == None:
                user = ctx.author
            await eco.create_user_info(user.id)
            embed = discord.Embed(title="Solde d'orbes oni",
                                  color=discord.Color.orange()   
                                  )
            embed.set_author(name=user.name, icon_url=user.display_avatar.url)
            embed.add_field(name="Orbes oni :", value=f"{ecof[str(user.id)]} orbes oni")
            embed.set_footer(text="pas d’inquiétude cher utilisateur, elles serviront plus tard soit dans un shop soit dans un classement ou les 2 qui sait?")
            return await ctx.send(embed=embed)

    @commands.hybrid_command(name="pay")
    async def orbe(self, ctx, user: discord.Member, amount: int):
        """
        New ✨!  Permet de donner des orbes à un utilisateur!
        """
        balance = await eco.get_balance(ctx.author.id)
        if balance >= amount:
            await eco.add(ctx.author.id, -amount)
            await eco.add(user.id, amount)
            succes_embed = discord.Embed(
                title = "Payement réussie",
                description = f"Vous venez de donner {amount} à {user.display_name}",
                color = discord.Color.yellow()
            )
            succes_embed.set_footer(text=f"Il vous reste {balance-amount} orbes.")
            return await ctx.send(embed=succes_embed)
        else:
            fail_embed = discord.Embed(
                title = "Payement refusé",
                description = f"Vous n'avez pas asser d'orbes pour donner {amount} à {user.display_name}\nVous n'en avez que {balance}",
                color = discord.Color.yellow()
            )
            return await ctx.send(embed=fail_embed)
    


async def setup(bot):

    await bot.add_cog(economy(bot))
