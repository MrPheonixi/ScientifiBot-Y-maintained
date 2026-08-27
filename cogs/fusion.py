import discord
from discord.ext import commands
import bot_package.Custom_func as Cf
import bot_package.data as data

class Fusion(commands.Cog):
    """
    Permet de fusionner des yokai et des objets.
    """

    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="fusion")
    async def fusion(self, ctx:commands.Context , item_or_yokai_a:str, item_or_yokai_b:str):
        """
        FUUUUUUUUUUUUSIONNNNNNNNN
        """
        fusion = f"{item_or_yokai_a},{item_or_yokai_b}"
        if not fusion in data.fusion.keys():
            fusion = f"{item_or_yokai_b},{item_or_yokai_a}"
            if not fusion in data.fusion.keys():
                fail_embed = discord.Embed(
                    title="Cette fusion n'existe pas.",
                    description=f"La fusion entre {item_or_yokai_a} et {item_or_yokai_b} n'existe pas.\nEssayez en une autre.",
                    color=discord.colour.Colour.red()
                )
                return await ctx.send(embed=fail_embed)
        item_A_type = data.fusion[fusion][item_or_yokai_a][0]
        if item_A_type == "yokai":
            where_type_A = "medallium"
            rang_item_A = data.fusion[fusion][item_or_yokai_a][1]
        else:
            where_type_A = "bag"
            rang_item_A = "obj"
        item_B_type = data.fusion[fusion][item_or_yokai_b][0]
        if item_B_type == "yokai":
            where_type_B = "medallium"
            rang_item_B = data.fusion[fusion][item_or_yokai_b][1]
        else:
            where_type_B = "bag"
            rang_item_B = "obj"
        if not await Cf.hasThing(ctx.author.id, item_or_yokai_a, where_type_A):
            not_has = discord.Embed(
                title="Vous n'avez pas l'objet/yokai A",
                description=f"Vous n'avez l'objet/yokai {item_or_yokai_a} dans votre {where_type_A}"
            )
            return await ctx.send(embed=not_has)
        if not await Cf.hasThing(ctx.author.id, item_or_yokai_b, where_type_B):
            not_has = discord.Embed(
                title="Vous n'avez pas l'objet/yokai B",
                description=f"Vous n'avez l'objet/yokai {item_or_yokai_b} dans votre {where_type_B}"
            )
            return await ctx.send(embed=not_has)

        bag = await Cf.get_bag(ctx.author.id)
        if fusion not in bag["trophe_data"]["fusion"]:
            bag["trophe_data"]["fusion"].append(fusion)
            bag["trophe_data"]["data"]["fusion"] = len(bag["trophe_data"]["fusion"])
            await Cf.save_bag(bag, ctx.author.id)
            await Cf.check_trophe(ctx.author.id, ctx)
        
        
        await Cf.remove(ctx.author.id, item_or_yokai_a, rang_item_A ,where_type_A)
        await Cf.remove(ctx.author.id, item_or_yokai_b, rang_item_B ,where_type_B)

        result = next(iter(data.fusion[fusion]["Result"])) #thanks ChatGPT
        result_type = data.fusion[fusion]["Result"][result][0]
        if result_type == "yokai":
            class_id = data.fusion[fusion]["Result"][result][1]
            class_name = await Cf.classid_to_class(class_id)
            try:
                yokai_embed = discord.Embed(
                    title=f"Vous avez eu le Yo-kai **{result}** ✨ ",
                    description=f"Félicitations il est de rang **{class_name}**",
                    color=discord.Color.from_str(data.yokai_data[class_id]["color"])
                )
            except KeyError:
                yokai_embed = discord.Embed(
                    title=f"Vous avez eu le Yo-kai **{result}** ✨ ",
                    description=f"Félicitations il est de rang **{class_name}**",
                    color=discord.Color.from_str(data.yokai_event_data[class_id]["color"])
                )
            yokai_embed.set_thumbnail(url=data.image_link[class_id])
        

            #define the id and so the api request to the image
        
            id = data.yokai_list_full.get(result, {}).get("id", None)
            yokai_embed.set_image(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id}.png")
            if id == None :
                yokai_embed.add_field(name="Image non disponible ! 😢", inline=False, value="En effet, nous ne possédons pas l'image de tous les Yo-kai, mais l'équipe travaille pour les apporter au complet et au plus vite.")


                
            if await Cf.hasThing(ctx.author.id, result, "medallium"):
                await Cf.add(ctx.author.id, result, class_id, "medallium", rank_orbe = True)
                inv = await Cf.get_inv(ctx.author.id)
                yokai_embed.add_field(
                    name=f"Vous l'avez déjà eu. Vous en avez donc {inv[result][1]}",
                    value="Faites `/medallium` pour voir votre Médallium."
                )
                yokai_embed.add_field(
                    name="vous l'avez déjà eu, dommage.",
                    value=f"voici {data.class_to_point[class_id]} orbes oni en cadeau."
                )
                    

            else:
                await Cf.add(ctx.author.id, result, class_id, "medallium")
                yokai_embed.add_field(
                    name="Vous ne l'avez jamais eu ! 🆕",
                    value="Il a été ajouté à votre Médallium. Faites `/medallium` pour le voir."
                )
                
            yokai_embed.set_footer(text=f"Fusion réussie !")
            return await ctx.send(embed=yokai_embed)
        

        else:
            #add the item to the bag
            await Cf.add(ctx.author.id, result, "obj", "bag")
            bag = await Cf.get_bag(ctx.author.id)
            item_desc = data.item[result]["desc"]

            item_embed = discord.Embed(
                title="Vous avez eu un objet 📦 ! ",
                description=f"> **{result}**",
                color=discord.Color.from_str("#674202")
            )
            #get the image

            id = data.item[result]["id"]
            item_embed.set_image(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id}.png")
                
            if await Cf.hasMoreThanOneThing(ctx.author.id, result, "bag"):
                            
                item_embed.add_field(
                    name=f"Vous l'avez déjà eu. Vous en avez donc {bag[result][1]}",
                    value="Faites `/bag` pour voir votre sacoche."
                )
            else:
                item_embed.add_field(
                    name=f"Vous ne l'avez jamais eu !",
                    value="Faites `/bag` pour voir votre sacoche."
            )
                
            item_embed.add_field(name="Mhh, voici quelques informations 📜", inline=False, value=f"> {item_desc}")
            item_embed.set_footer(text=f"Fusion réussie!")
            await Cf.save_bag(bag, ctx.author.id)
            return await ctx.send(embed=item_embed)


async def setup(bot) -> None:
    await bot.add_cog(Fusion(bot))