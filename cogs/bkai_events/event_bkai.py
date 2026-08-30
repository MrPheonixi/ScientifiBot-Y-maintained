import discord
from discord.ext import commands

import random
import asyncio

import bot_package.Custom_func as Cf
import bot_package.economy as economy
import bot_package.data as data
import time

loot = data.terrheure




# def the button and its characteristics
class button(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=350)
        self.users_in = [ctx.author.id]

    @discord.ui.button(label='rejoindre la terrheure', style=discord.ButtonStyle.blurple, custom_id='join')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.users_in:
            await interaction.response.send_message("tu as rejoint la terr'heure !", ephemeral=True)
            self.users_in.append(interaction.user.id)
        else:
            await interaction.response.send_message("tu es déjà dans la terr'heure...", ephemeral=True)



class Terrheure():
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    async def terrheure(self,ctx:commands.Context):

        #defined the view(the button), the start of the embed, sent it and save his id
        view = button(ctx)
        embed = discord.Embed(title="La terr'heure a commencée !",
                              description=f"cliquez sur le bouton ci-dessous pour rejoindre la terr'heure ! \n plus le nombre de personne sera élevé, plus les récompenses seront grandes !",
                              color=discord.Color.dark_red())
        embed.add_field(name="Temps restant:", value=f"<t:{int(time.time())+300}:R>")
        embed.set_footer(text="merci de ne pas supprimer ce message")
        message = await ctx.send(embed=embed, view=view)
        
        self.bot.logger.info(f"Terrheure started in server {ctx.guild.id}/{ctx.guild.name}, started by {ctx.author.id}/{ctx.author.name}")

        # wait the end of the terrheure and edit the first embed
        await asyncio.sleep(300)
        embed_end = discord.Embed(title="La terr'heure est finie !",
                                  color=discord.Color.dark_red())
        embed_end.set_footer(text="merci de ne pas supprimer ce message")
        try:
            await message.edit(embed=embed_end, view=None)
        except discord.errors.NotFound:
            pass
        except discord.errors.Forbidden:
            pass
        

        # make a list with the mention of all the participants 
        list_part = ""
        for user in view.users_in:
            list_part += f"<@{user}> "
            
        
        # give the reward if the number of participant is equal or superior
        users_len = len(view.users_in)    
        
        end_embed = discord.Embed(title="fin de la terr'heure !", description=f"la terr'heure a réuni {users_len} participants !",
        color=discord.Color.green())
        end_embed.add_field(name="participants :", value=list_part,inline=False)
        
        
        
        for recompense in loot.keys():
            if recompense == "stats":
                # pass stats reward for not giving error
                continue
            if int(recompense) <= users_len:
                reward = loot[str(recompense)]

                # if reward is orbe use eco module to give it
                if reward["type"] == "orbe":
                    phrase = f"{reward["amount"]} orbes oni pour chaque personne"
                    for id in view.users_in:
                        await economy.add(id,reward["amount"])

                # if reward is yokair(yokai rang)
                # choose a random yokai in this rang and give him
                # use a shorter version of give in admin cog
                elif reward["type"] == "yokair":
                    gifted_yokai = random.choice(data.yokai_data[reward["class"]]["yokai_list"])
                    phrase = f"le yokai {gifted_yokai} de rang {reward["class"]}"
                    for id in view.users_in:
                        await Cf.add(id,gifted_yokai,reward["class"],"medallium")

                # if reward is a coin 
                # choose a random coin in a list
                # and give him with the shorter give
                elif reward["type"] == "coin":
                    gifted_coin = random.choice(loot[recompense]["coin_list"])
                    phrase = f"{reward["amount"]} {gifted_coin}"
                    for id in view.users_in:
                        await Cf.add(id, gifted_coin,"coin","bag", reward["amount"])

                # if reward is yokail (yokai list)
                # choose a random yokai in this list and give him
                # use a shorter version of give in admin cog
                elif reward["type"] == "yokail":
                    gifted_yokai = random.choice(reward["yokai_list"])
                    phrase = f"le yokai {gifted_yokai} de rang {reward["rang"]}"
                    for id in view.users_in:
                        await Cf.add(id,gifted_yokai,reward["rang"],"medallium")

                # if reward is treasure
                # give the selected treasure
                # use a shorter version of give in admin cog
                elif reward["type"] == "treasure":
                    phrase = f"le magnifique {reward["name"]}"
                    for id in view.users_in:
                        await Cf.add(id,reward["name"],"treasure","bag")


                # add a field to the embed corresponding of the reward of all stage
                end_embed.add_field(name=f"Récompenses pour avoir atteint {recompense} personnes:", value=phrase)
            else:
                break
        
        try:
            await message.reply(embed=end_embed)    
        except discord.NotFound:
            await ctx.send(embed=end_embed)
        except discord.Forbidden:
            pass
        
        self.bot.logger.info(f"Terrheure stopped in server {ctx.guild.id}/{ctx.guild.name}, started by {ctx.author.id}/{ctx.author.name}, {users_len} users")

        data.terrheure.setdefault("stats", {})
        data.terrheure["stats"]["activation_time"] = int(data.terrheure["stats"].get("activation_time", 0)) + 1
        data.save_json("./files/terrheure_loot.json", data.terrheure)

        for id in view.users_in:
            await Cf.update_trophe_data(id, "terrheure", 1, "add")
            if users_len >= 5:
                await Cf.update_trophe_data(id, "terrheure 5", 1, "add")
            if users_len >= 15:
                await Cf.update_trophe_data(id, "terrheure 15", 1, "add")
            if users_len >= 45:
                await Cf.update_trophe_data(id, "terrheure 45", 1, "add")
            await Cf.trophe_check(id, ctx)