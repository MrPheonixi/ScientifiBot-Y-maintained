import discord
from discord.ext import commands
import bot_package.Custom_func as Cf
import bot_package.economy as eco
import bot_package.data as data
import random
import time

if True: #flemme of removing all this tab
    async def generate_daily_shop(ctx):
        #obtient l'heure pour regarder si il faut un reset
        midnight = await Cf.get_midnight()

        bag = await Cf.get_bag(ctx.author.id)
        if bag == {}:
            bag = data.default_bag.copy()

        try:
            last_daily_shop_reset = bag["daily_shop_data"][1]
        except KeyError:
            last_daily_shop_reset = 0
        
        if last_daily_shop_reset < midnight: #select the item if he didn't get choose this day
            last_daily_shop_reset = midnight
            possible_daily_item_type = ["coin", "object", "yo-kai"]
            daily_item_type = random.choice(possible_daily_item_type) #choose the type of the item

            if daily_item_type == 'coin':
                coin_type = random.choices(["normal","rare"],weights=[0.75,0.25])[0] #choose to get a normal or a rare coin

                if coin_type == 'normal':
                    daily_item = random.choice(data.daily_shop["low_cost_coin_list"])
                    price = data.daily_shop["low_cost_coin"] #get the price for a normal coin

                elif coin_type == 'rare':
                    daily_item = random.choice(data.daily_shop["high_cost_coin_list"])
                    price = data.daily_shop["high_cost_coin"] #get the price for a rare coin

                description = "Une petite-pièce à utiliser au /bkai."
                type_daily_shop = "coin"
                data_daily_shop = [last_daily_shop_reset, type_daily_shop, price, description, daily_item] #save all the data


            elif daily_item_type == 'object':
                daily_item = random.choice(list(data.item.keys())) #get the object
                price = data.daily_shop["price_daily_shop_object"] #get the price for an object
                type_daily_shop = "object"
                description = "Un objet en vente."
                if data.item[daily_item]["type"] == "treasure":
                    price = 1000
                data_daily_shop = [last_daily_shop_reset, type_daily_shop, price, description, daily_item] #save all the data


            elif daily_item_type == 'yo-kai':
                weights=data.daily_shop["daily_shop_proba_yokai"].copy() #will do a bingo-kai roll, but with better luck
                class_choice = data.yokai_data[random.choices(data.class_list, weights=weights, k=1)[0]]
                while class_choice["class_name"] in data.blacklist["rang"]:
                    class_choice = data.yokai_data[random.choices(data.class_list, weights=weights, k=1)[0]]

                #get the good name of the class and his id
                class_name = class_choice.get("class_name")
                class_id = class_choice.get("class_id")
                #choose the Yo-kai in the class
                Yokai_choice = random.choice(class_choice["yokai_list"])
        
                while Yokai_choice in data.blacklist.get("yokai") :
                    Yokai_choice = random.choice(class_choice["yokai_list"])
                Yokai_choice = Yokai_choice
                description = f"Un magnifique yo-kai de rang {class_name}✨"
                type_daily_shop = "yokai"
                price = data.daily_shop["classid_to_price"][class_id]
                data_daily_shop = [last_daily_shop_reset, type_daily_shop, price, description, Yokai_choice, class_id] #save all the data
                

            
            data_daily_shop.insert(0, False)
            bag["daily_shop_data"] = data_daily_shop
            embed = discord.Embed(
                title="Votre item du jour dans la boutique:",
                description="",
                color=discord.Color.from_str("#674202")
            )

            description = bag["daily_shop_data"][4]
            price = bag["daily_shop_data"][3]
            daily_item = bag["daily_shop_data"][5]

            if bag["daily_shop_data"][2] == "yokai":       #make the embed for the yokai
                class_id = bag["daily_shop_data"][6]
                class_name = await Cf.classid_to_class(class_id)

                embed.add_field(name = f"{daily_item}",value = f"Rang: {class_name} \nDescription: {description} \nPrix: {price} orbes")
                embed.set_thumbnail(url=data.image_link[class_id])
                id = data.yokai_list_full.get(daily_item, {}).get("id", None)
                embed.set_image(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id}.png")

            else:      #make the embed for object or coin
                embed.add_field(name = f"{daily_item}",value = f"Description: {description} \nPrix: {price} orbes")


            await Cf.save_bag(bag,ctx.author.id)

class shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    


    @commands.hybrid_command(name="shop")
    async def shop(self, ctx, page:str ="1"):
        '''
        Permet de visualiser les items disponibles dans le shop page par page
        '''
        actual_shop = data.shop_item

        try:
            page = int(page)
        except ValueError:
            return await ctx.send(embed=discord.Embed(title="Erreur", description="Veuillez entrer un numéro de page valide.", color=discord.Color.red()))
        if page < 1 or page > len(actual_shop):
            return await ctx.send(embed=discord.Embed(title="Erreur", description=f"Veuillez entrer un numéro de page valide.", color=discord.Color.red()))
        print("Shop command executed")



        embed = discord.Embed(title="Shop",
                          description="Welcome to the shop! Here are the available items:",
                          color=discord.Color.blue())
        if page == 1:  #show the daily item on the first page
            await generate_daily_shop(ctx)
            bag = await Cf.get_bag(ctx.author.id)
            item_type = bag["daily_shop_data"][2]
            description = bag["daily_shop_data"][4]
            price = bag["daily_shop_data"][3]
            item = bag["daily_shop_data"][5]
            if item_type == "yokai":
                class_name = await Cf.classid_to_class(bag["daily_shop_data"][6])
                embed.add_field(name=f"Item du jour:\n{item}, yo-kai de rang {class_name}", value=f"Prix: {price} orbes\nDescription: {description}", inline=False)
            else:
                embed.add_field(name=f"Iem du jour\n{item}", value=f"Prix: {price} orbes\nDescription: {description}", inline=False)
            embed.set_footer(text=f"Page {page}/{len(actual_shop.keys())}")

        for item in actual_shop[f"page {page}"]:
            item_data = actual_shop[f"page {page}"][item]
            price = item_data.get("price")
            description = item_data.get("description", "")
            amount = item_data.get("quantity")
            embed.add_field(name=f"{item} X{amount}", value=f"Prix: {price} orbes\nDescription: {description}", inline=False)
            embed.set_footer(text=f"Page {page}/{len(actual_shop.keys())}")
        return await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy")
    async def buy(self, ctx, item: str):
        '''
        Permet d'acheter un item du shop
        '''
        actual_shop = data.shop_item
        item_found = False
        print(f"Buy command executed for item: {item}")
        for page_items in actual_shop.values():
            if item in page_items:
                item_found = True
                page = page_items
                break
        if not item_found:
            return await ctx.send(embed=discord.Embed(title="Erreur", description=f"L'item {item} n'est pas disponible dans le shop.\nMerci de rentrer un item valide.", color=discord.Color.red()))
        else:
            user_balance = await eco.get_balance(ctx.author.id)
            item_info = page[item]
            price = item_info.get("price", 0)
            rang = item_info.get("rang", "obj")
            print(rang)
            quantity = item_info.get("quantity", 1)

            if user_balance < price:
                embed_poor = discord.Embed(title="Erreur", description=f"Vous n'avez pas assez d'orbes pour acheter {item}.", color=discord.Color.red())
                embed_poor.set_footer(text=f"vous avez {user_balance}/{price} orbes") 
                return await ctx.send(embed=embed_poor)
            else:
                await eco.add(ctx.author.id, -price)
                await Cf.add(ctx.author.id, item, rang, "bag", number=quantity)
                embed = discord.Embed(title="Achat réussi", description=f"Vous avez acheté {item} pour {price} orbes.", color=discord.Color.green())
                return await ctx.send(embed=embed)
            

    @commands.hybrid_command(name="daily_shop")
    async def daily_shop(self, ctx):
        """
        New ✨! Permet de voir votre item du jour dans la boutique.
        """

        await generate_daily_shop(ctx)

        bag = await Cf.get_bag(ctx.author.id)
        
        #show the item
        daily_item = bag["daily_shop_data"][5]
        embed = discord.Embed(
            title="Votre item du jour dans la boutique:",
            description="",
             color=discord.Color.from_str("#674202")
        )

        description = bag["daily_shop_data"][4]
        price = bag["daily_shop_data"][3]

        if bag["daily_shop_data"][2] == "yokai":
            class_id = bag["daily_shop_data"][6]
            class_name = await Cf.classid_to_class(class_id)
            Yokai_choice = bag["daily_shop_data"][5]

            embed.add_field(name = f"{daily_item}",value = f"Rang: {class_name} \nDescription: {description} \nPrix: {price} orbes")
            embed.set_thumbnail(url=data.image_link[class_id])
            id = data.yokai_list_full.get(Yokai_choice, {}).get("id", None)
            embed.set_image(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id}.png")

        else:
            embed.add_field(name = f"{daily_item}",value = f"Description: {description} \nPrix: {price} orbes")

        return await ctx.send(embed=embed)


    @commands.hybrid_command(name="buy_daily")
    async def buy_daily(self, ctx):
        """
        New ✨! Permet d'acheter votre item du jour dans la boutique.
        """
       
        await generate_daily_shop(ctx)

        bag = await Cf.get_bag(ctx.author.id)

        if bag == {}:
            bag = data.default_bag.copy()
            verification = False
        else:
            verification = True


        balance = await eco.get_balance(ctx.author.id) #get the balance
        price = bag["daily_shop_data"][3] #get the price

        if bag["daily_shop_data"][0] == True:   #check if the item was already bough
            embed = discord.Embed(
                title="Achat impossible",
                description="Vous avez déja acheté votre item quotidien. Réessayer demain.",
                color=discord.Color.red()
                )
            return await ctx.send(embed=embed)
        

        elif balance >= price:
            if bag["daily_shop_data"][2] == "object":
                item = bag["daily_shop_data"][5]
                item_type = data.item[item]["type"]
                item_desc = data.item[item]["desc"]
                
                if verification:
                    for elements in bag.keys():
                        if elements == item:
                            verification = False
                            try:
                                bag[item][1] += 1
                            except IndexError:
                                bag[item].append(2)
                                
                            #make the embed
                            item_embed = discord.Embed(
                                title="Vous avez acheté un objet 📦 ! ",
                                description=f"> **{item}**",
                                color=discord.Color.from_str("#674202")
                            )
                            #get the image

                            id = data.item[item]["id"]
                            item_embed.set_image(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id}.png")
                            
                            item_embed.add_field(
                                name=f"Vous l'avez déjà eu. Vous en avez donc {bag[item][1]}",
                                value="Faites `/bag` pour voir votre sacoche."
                            )
                            item_embed.add_field(name="Mhh, voici quelques informations 📜", inline=False, value=f"> {item_desc}")
                            item_embed.set_footer(text=f"Achat quotidien réalisé!")
                            await eco.add(ctx.author.id, -price)
                            bag["daily_shop_data"][0] = True
                            await Cf.save_bag(bag,ctx.author.id)
                            return await ctx.send(embed=item_embed)

                if verification:
                    bag[item] = [item_type]
                    try:
                        bag[item_type] += 1
                    except KeyError:
                        bag[item_type] = 1
                    item_embed = discord.Embed(
                        title="Vous avez acheté un objet 📦 ! ",
                        description=f"> **{item}**",
                        color=discord.Color.from_str("#674202")
                    )
                    #get the image

                    id = data.item[item]["id"]
                    item_embed.set_image(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id}.png")
                    
                    item_embed.add_field(
                        name=f"Vous ne l'avez jamais eu !",
                        value="Faites `/bag` pour voir votre sacoche."
                    )
                    item_embed.add_field(name="Mhh, voici quelques informations 📜", inline=False, value=f"> {item_desc}")
                    
                    item_embed.set_footer(text=f"Achat quotidien réalisé!")
                    await eco.add(ctx.author.id, -price)
                    bag["daily_shop_data"][0] = True
                    await Cf.save_bag(bag,ctx.author.id)
                    return await ctx.send(embed=item_embed)

            elif bag["daily_shop_data"][2] == "coin":
                coin = bag["daily_shop_data"][5]
                coin_color = data.coin_data[coin]["color"]
                coin_id = data.coin_data[coin]["id"]
            
                coin_embed = discord.Embed(
                    title=f"Vous avez acheté une {coin}!",
                    description=f"Pour l'utiliser, faites un `/bingo-kai {coin}`.\n-# A savoir: le /bkai avec des pièces n'a pas de cooldown, juste une limite journalière (=>vous pouvez le spam tant que vous avez des pièces)",
                    color=discord.Color.from_str(coin_color)
                )
            
                #add the image
                coin_embed.set_image(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{coin_id}.png")

            
                if verification == True:
                    #get all the coins
                    for elements in bag.keys():
                        if elements == coin:
                            #stack the coin
                            try:
                            #stack the Yo-kai
                                bag[coin][1] += 1
                            except IndexError:
                                bag[coin].append(2)
                            verification = False

                         #Generate the rest of the embed
                            coin_embed.add_field(
                                name=f"Vous l'avez déjà eu. Vous en avez donc {bag[coin][1]}",
                                value="Faites `/bag` pour voir votre sacoche."
                            )

                    if verification == True:  
                        bag[coin] = ["coin"]
                        bag["coin"] += 1
                        coin_embed.add_field(
                            name="Vous ne l'avez jamais eu !",
                            value="Elle a été ajoutée à votre sacoche. Faites `/bag` pour la voir."
                        )
                await eco.add(ctx.author.id, -price)
                bag["daily_shop_data"][0] = True
                await Cf.save_bag(bag,ctx.author.id)
                coin_embed.set_footer(text=f"Achat quotidien réalisé!")
                return await ctx.send(embed=coin_embed)
            
            elif bag["daily_shop_data"][2] == "yokai":
                Yokai_choice = bag["daily_shop_data"][5]
                class_id = bag["daily_shop_data"][6]
                class_name = await Cf.classid_to_class(class_id)
                brute_inventory = await Cf.get_inv(ctx.author.id)

                yokai_embed = discord.Embed(
                    title=f"Vous avez acheté le Yo-kai **{Yokai_choice}** ✨ ",
                    description=f"Félicitations il est de rang **{class_name}**",
                    color=discord.Color.from_str(data.yokai_data[class_id]["color"])
                )
                yokai_embed.set_thumbnail(url=data.image_link[class_id])
                id = data.yokai_list_full.get(Yokai_choice, {}).get("id", None) #I feel ashamed of what I did here
                yokai_embed.set_image(url=f"https://lfbn-idf3-1-5-236.w81-249.abo.wanadoo.fr/{id}.png")

                #is the Yo-kai in the inventory
                #try the inv

                if verification == True:
                    #get all the yokais
                    for elements in brute_inventory.keys():
                        if elements == Yokai_choice:
                            verification = False
                            try:
                                #stack the Yo-kai
                                brute_inventory[Yokai_choice][1] += 1
                            except IndexError:
                                brute_inventory[Yokai_choice].append(2)

                            #Generate the embed
                            yokai_embed.add_field(
                                name=f"Vous l'avez déjà eu. Vous en avez donc {brute_inventory[Yokai_choice][1]}",
                                value="Faites `/medallium` pour voir votre Médallium."
                            )
                            
                            #SAVE the inv
                            await Cf.save_inv(brute_inventory, ctx.author.id)                            



                    if verification == True:
                        brute_inventory[Yokai_choice] = [class_id]
                        try:
                            brute_inventory[class_id] += 1
                        except KeyError:
                            brute_inventory[class_id] = 1
                        brute_inventory["last_claim"] = time.time()
                        await Cf.save_inv(brute_inventory, ctx.author.id)
                        yokai_embed.add_field(
                            name="Vous ne l'avez jamais eu ! 🆕",
                            value="Il a été ajouté à votre Médallium. Faites `/medallium` pour le voir."
                        )

                else:
                    brute_inventory[Yokai_choice] = [class_id]
                    try:
                        brute_inventory[class_id] += 1
                    except KeyError:
                        brute_inventory[class_id] = 1
                    await Cf.save_inv(brute_inventory, ctx.author.id)
                    yokai_embed.add_field(
                        name="Vous ne l'avez jamais eu ! 🆕",
                        value="Il a été ajouté à votre Médallium. Faites `/medallium` pour le voir."
                    )

                await eco.add(ctx.author.id, -price)
                bag["daily_shop_data"][0] = True      #the item can be bough only one time/day
                await Cf.save_bag(bag,ctx.author.id)
                yokai_embed.set_footer(text=f"Achat quotidien réalisé!")

                return await ctx.send(embed=yokai_embed)


        else:   #make a message if the person doesn't have enough money for buy the item
            poor_embed = discord.Embed(
                title="Tu ne peux pas acheter cela",
                description=f"Tu n'as pas assez d'argent pour acheter cela.\nIl te faut {price} orbes, mais tu n'as que {balance} orbes.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=poor_embed)


async def setup(bot) -> None:
    await bot.add_cog(shop(bot))
    
