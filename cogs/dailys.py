import discord
from discord.ext import commands
import bot_package.Custom_func as Cf
import bot_package.data as data
import random
import datetime


class daily(commands.Cog):

    @commands.hybrid_command(name="daily")
    async def daily(self, ctx: commands.Context):
        """
        permet de récupérer un objet une fois par jour
        """
        #on charge les donnée nessécaire
        people = data.daily_people

        #on vérifie si on a changé de jours
        today = str(datetime.date.today())[-2:]
        print(today)
        print(people["day"])
        if people["day"] != today:
            people["day"] = today
            people["people"].clear()
        
        #on vérifie si le joueur a récupéré son dailys aujourd'hui
        if ctx.author.id in people["people"]:
        #on lui envoi un gentil message pour lui dire qu'il en aura pas 2
            embed_bad_people = discord.Embed(title="Vous avez déjà récupéré votre récompense aujourd'hui",
                                             description="Ce n'est pas grave revenez demain !",
                                             colour=discord.Color.from_rgb(255,0,0))
            embed_bad_people.set_footer(text="La réinitialisation s'effectue tous les soirs à minuit.")
            return await ctx.send(embed=embed_bad_people)
        #si non on le note
        people["people"].append(ctx.author.id)
        data.save_json("./files/daily.json", people)
        
        #on défini quelque liste pour bien choisir l'objet
        prize = ["Pièce Journalière","color coin","rare coin"]
        weights = [75,20,5]
        

        color_coin=["Pièce rouge","Pièce jaune","Pièce orange","Pièce rose","Pièce verte","Pièce bleue","Pièce mauve","Pièce bleue ciel"]
        rare_coin=["Pièce 5 étoiles","Pièce spéciale","Pièce noire","Pièce démoniaque","Pièce scellée","Pièce légendaire","Pièce monstrueuse"]
        
        #on choisi l'objet
        choice = random.choices(prize,weights=weights)[0]
        if choice =="color coin":
            choice = random.choice(color_coin)[0]

        elif choice == "rare coin":
            choice = random.choice(rare_coin)[0]
        print(choice)
        choice = str(choice)
        print(choice)
            
        #on lui give
        await Cf.add(ctx.author.id,choice,"coin","bag")

        #on affiche le message
        embed=discord.Embed(title="Vous avez récupéré votre Pièce journalière!",
                            description=f"C'est une simple {choice} mais cela devrait suffir pour aujourd'hui",
                            colour=discord.Color.green())
        embed.set_footer(text="Reviens demain pour recevoir une autre pièce")
        return await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(daily(bot))