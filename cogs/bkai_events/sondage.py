import asyncio

import discord
import bot_package.data as data
import bot_package.Custom_func as cf
from PIL import image as pil
import time
import requests
import random

async def sondage(ctx,bot, user_id):
    #get the sondage data
    sondage_data = data.open_json("./files/sondage.json")
    cs = sondage_data["current_stage"]
    need_reset = False
    #get the last day of poll
    last_day = sondage_data["last_day"]
    #get the current day
    current_day = time.datetime.date
    if last_day != current_day:
        sondage_data["last_day"] = current_day
        need_reset = True
    if need_reset:
        # post the result of the poll in the poll channel
        poll_channel = bot.get_channel(data.config_data["poll_channel_id"])
        if sondage_data["choice2"] > sondage_data["choice1"]:
            temp = sondage_data["last_selection1"]
            sondage_data["last_selection1"] = sondage_data["last_selection2"]
            sondage_data["last_selection2"] = temp
            temp = sondage_data["choice1"]
            sondage_data["choice1"] = sondage_data["choice2"]
            sondage_data["choice2"] = temp
            
        poll_embed = discord.Embed(title="Résultat du sondage d'hier !",
                                   description=f"Le sondage d'hier a été remporté par {sondage_data['last_selection1']} avec {sondage_data['choice1']} votes contre {sondage_data['last_selection2']} avec {sondage_data['choice2']} votes !",
                                   color=discord.Color.green())
        
        #crée la liste suivante si non existante
        #mettre le gagnant dans la list
        #si il reste que un yk dans la current list, le faire passer ainsi que le notifier
        #et si c'est le cas changer le current stage
        last_day_img = pil.open(f"./files/poll_image/{last_day}.png")
        poll_embed.set_image(last_day_img)
        await poll_channel.send(embed=poll_embed)
        # reset the poll data for the new day
        sondage_data["last_day"] = current_day
        sondage_data["choice1"] = 0
        sondage_data["choice2"] = 0
        #choose 2 new yokai and make other stuff
        yk1 = random.choice(sondage_data[cs])
        sondage_data[cs].remove(yk1)
        yk2 = random.choice(sondage_data[cs])
        sondage_data[cs].remove(yk2)
        sondage_data["last_selection1"] = yk1
        sondage_data["last_selection2"] = yk2

        #create the poll image
        id_list = data.yokai_list_full
        id1 = id_list[yk1]["id"]
        id2 = id_list[yk2]["id"]
        imgyk1 = requests.get(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id1}.png")
        imgyk2 = requests.get(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id2}.png")
        im = pil.image.new("rgba",(1024,512))
        im.paste(imgyk1, (0,0))
        im.paste(imgyk2, (512,0))
        vs = pil.open("./files/poll_image/vs.png")
        im.paste(vs, (256,0))
        im.save(f"./files/poll_image/{current_day}.png")
    if str(user_id) in sondage_data["today_user"]:
        embed = discord.Embed(title="Vous avez déjà participé au sondage aujourd'hui !", color=discord.Color.red())
        return await ctx.send(embed=embed, ephemeral=True)
    else:
        sondage_data["today_user"].append(str(user_id))
        data.save_json("./files/sondage.json", sondage_data)
        poll_embed = discord.Embed(title="Sondage du jour !",
                                   description=f"Votez pour ton yokai préféré !\n\n{sondage_data['last_selection1']} ou {sondage_data['last_selection2']} ?",
                                   color=discord.Color.blue())
        im = pil.open(f"./files/poll_image/{current_day}.png")
        poll_embed.set_image(im)
        msg = await ctx.send(embed=poll_embed, ephemeral=True)
        
        await msg.add_reaction("1️⃣")
        await msg.add_reaction("2️⃣")

        def check(reaction, user):
            return (
                user != bot.user
                and reaction.message.id == msg.id
                and str(reaction.emoji) in ("1️⃣", "2️⃣")
            )

        try:
            reaction, user = await bot.wait_for(
                "reaction_add",
                timeout=30,
                check=check
            )

            if str(reaction.emoji) == "1️⃣":

                sondage_data["choice1"] += 1
            else:
                sondage_data["choice2"] += 1
            cf.save_json("./files/sondage.json", sondage_data)
            await ctx.send("Merci pour votre vote !", ephemeral=True)

        except asyncio.TimeoutError:
            await ctx.send("Temps écoulé, aucun choix.")

    
    