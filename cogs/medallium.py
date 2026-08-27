import discord
from discord.ext import commands
import bot_package.Custom_func as Cf
import bot_package.data as data






#Medallium command cog
class Medallium(commands.Cog) :
    """
    Permet de voir votre Médallium (inventaire), tous les Yo-kai que vous avez eu avec le /bingo-kai et votre sacoche avec tous vos objets et pièces.
    """
    
    
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        
        
    @commands.hybrid_command(name="medallium")
    async def medallium(self, ctx = commands.Context, user : discord.User = None ):
        """
        Permet de voir votre Médallium (inventaire), tous les Yo-kai que vous avez eu avec le /bingo-kai. 
        Utilisez */medallium {user}* pour voir le Médallium d'un autre utilisateur.
        """
        #define the user
        if user == None:
            user = ctx.author

        #Get inventory
        brute_inventory = await Cf.get_inv(user.id)

        #try if the inv is empty
        if brute_inventory == {}:
            if user.id == ctx.author.id:
                inv_embed = discord.Embed(title="Oops, votre Médallium est vide 😢!")
            else:
                inv_embed = discord.Embed(title=f"Oops, le Médallium de {user.name} est vide 😢!")
            return await ctx.send(embed=inv_embed)

        #create the list :  
        yokai_per_class = {
            "E": {},
            "D": {},
            "C": {},
            "B": {},
            "A": {},
            "S": {},
            "treasureS": {},
            "SpecialS": {},
            "LegendaryS": {},
            "DivinityS": {},
            "Boss": {},
            "Shiny": {}
        }

        
        blacklist = ["streak"]
        
        #sort the Yo-kai by class
        for elements in brute_inventory:
            #Don't take any numbers
            if not type(brute_inventory[elements]) == int and not type(brute_inventory[elements]) == float and not elements in blacklist and elements not in data.yokai_event_list:
                categorie = brute_inventory[elements]

                #Check if it's stack
                try:
                    count = brute_inventory[elements][1]
                except:
                    count = 1

                #add it to the right list
                yokai_per_class[categorie[0]][elements] = count

        #sort the list alphabeticaly :
        for non_sorted_dicts in yokai_per_class:
            list_key = list(yokai_per_class[non_sorted_dicts].keys())
            list_key.sort()

            sorted_dict = {i: yokai_per_class[non_sorted_dicts][i] for i in list_key}
            yokai_per_class[non_sorted_dicts] = sorted_dict

        #define the emoji list
        emoji = data.emoji
        yokai_data = data.yokai_data
        list_len = data.list_len
        image_link = data.image_link




        #Inv dropdown class
        class Inv_dropdown(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label="Tout !", description="Affiche tout le Médallium si possible.", emoji="🌐"),
                    discord.SelectOption(label="E", emoji=emoji["E"]),
                    discord.SelectOption(label="D", emoji=emoji["D"]),
                    discord.SelectOption(label="C", emoji=emoji["C"]),
                    discord.SelectOption(label="B", emoji=emoji["B"]),
                    discord.SelectOption(label="A", emoji=emoji["A"]),
                    discord.SelectOption(label="S", emoji=emoji["S"]),
                    discord.SelectOption(label="Légendaire", emoji=emoji["LegendaryS"]),
                    discord.SelectOption(label="Trésor", emoji=emoji["treasureS"]),
                    discord.SelectOption(label="Spécial", emoji=emoji["SpecialS"]),
                    discord.SelectOption(label="Divinité / Enma", emoji=emoji["DivinityS"]),
                    discord.SelectOption(label="Boss", emoji=emoji["Boss"]),
                    discord.SelectOption(label="Shiny", emoji="✨")
                ]

                super().__init__(placeholder='Choisissez le rang que vous voulez...', min_values=1, max_values=1, options=options)

            async def callback(self, interaction, ctx=ctx):
                if self.values[0] == "Tout !":
                    if user.id == ctx.author.id:
                        inv_embed = discord.Embed(title="Voici votre Médallium :")
                    else:
                        inv_embed = discord.Embed(title=f"Voici le Médallium de {user.name} :")

                    try:
                        for classes in yokai_per_class:
                            yokai_list_brute = yokai_per_class[classes]
                            classes_name = await Cf.classid_to_class(classes, False)
                            class_id = classes

                            yokai_list_formated = ""

                            if yokai_list_brute != {}:
                                for elements in yokai_list_brute:
                                    if yokai_list_brute[elements] > 1:
                                        yokai_list_formated += f"> {elements} **`(x{str(yokai_list_brute[elements])})`**\n"
                                    else:
                                        yokai_list_formated += f"> {elements}\n"

                                inv_embed.add_field(name=f"Rang {classes_name} `{brute_inventory[class_id]}/{list_len[class_id]}`",
                                                    value=yokai_list_formated)
                                inv_embed.set_author(name=f"Médallium de {user.name}")
                        return await interaction.response.send_message(embed=inv_embed)
                    #if the medallium is to big to be in one message
                    except discord.errors.HTTPException as e:
                        try:
                            async def get_yokai_list(yo_kai_show, yokai_per_class):

                                yokai_list_formated = ""

                                for classes in yokai_per_class:
                                    yokai_list_brute = yokai_per_class[classes]
                                    classes_name = await Cf.classid_to_class(classes, False)
                                    class_id = classes
                                
                                    if class_id in yo_kai_show:

                                        yokai_list_formated += f"# __**Rang {classes_name}:**__\n"

                                        if yokai_list_brute != {}:
                                            for elements in yokai_list_brute:
                                                if yokai_list_brute[elements] > 1:
                                                    yokai_list_formated += f"> {elements} **`(x{str(yokai_list_brute[elements])})`**\n"
                                                else:
                                                    yokai_list_formated += f"> {elements}\n"
                                return yokai_list_formated
                            
                            
                            
                                    
                            #the message for select the page.
                            #Page one: Every yo-kai of class E, D and C
                            #Page two: Every yo-kai of class B and A
                            #Page three: Every yo-kai of class S, tresure, special, legendary, boss, divinity and shiny
                            class Inv_all(discord.ui.Select):
                                def __init__(self):
                                    options = [
                                    discord.SelectOption(label="Page 1", description="Affiche la page 1 du médallium.", emoji="1️⃣"),
                                    discord.SelectOption(label="Page 2", description="Affiche la page 2 du médallium.", emoji="2️⃣"),
                                    discord.SelectOption(label="Page 3", description="Affiche la page 3 du médallium.", emoji="3️⃣"),
                                    ]

                                    super().__init__(placeholder='Choisissez la page du Médallium que vous voulez...', min_values=1, max_values=1, options=options)
                                async def callback(self, interaction, ctx=ctx):
                                    try:
                                        #list of classes per pages
                                        if self.values[0] == "Page 1":
                                            yo_kai_show = ["E","D", "C"]
                                        elif self.values[0] == "Page 2":
                                            yo_kai_show = ["B","A"]
                                        elif self.values[0] == "Page 3":
                                            yo_kai_show = ["S","treasurS","SpecialS", "LegendaryS", "DivinityS", "Boss", "Shiny"]

                                        yokai_list_formated = await get_yokai_list(yo_kai_show, yokai_per_class)

                                        #create the embed
                                        inv_embed = discord.Embed( 
                                            title=f"__Médallium - {self.values[0]}:__",
                                            description=yokai_list_formated,
                                            color=discord.colour.Color.orange()
                                            )
                                        return await interaction.message.edit(embed=inv_embed) #change the message send before for not flood the channel
                                         
                                    #in case there is to many yo-kai, shouldn't be the case but who know? Edit: it's the case for nearly 100% medallium
                                    except discord.errors.HTTPException:
                                        error_embed = discord.Embed(color=discord.Color.red(),
                                            title="Oh non, une erreur s'est produite !",
                                            description="> Un bug sur cette commande se produit quand le Médallium est trop grand pour être affiché. (C'est un peu un flex quand même 🙃)")
                                        error_embed.add_field(name="Vous devez donc spécifier un rang pour que cela marche.",
                                            value="Vous pouvez utiliser le message ci-dessus.")
                                        return await interaction.response.send_message(embed=error_embed)


                            class Inv_all_view(discord.ui.View):
                                def __init__(self):
                                    super().__init__(timeout=300)
                                    self.add_item(Inv_all())
                                async def on_timeout(self):
                                    for item in self.children:
                                        item.disabled = True
                                    try:
                                        await self.message.edit( embed=self.message.embeds[0], view=self)
                                    except discord.NotFound:
                                        pass
                                    
                            Dropdown = Inv_all_view()

                            yo_kai_show = ["E","D","C"]

                            yokai_list_formated = await get_yokai_list(yo_kai_show, yokai_per_class)

                            main_embed = discord.Embed(title="__Médallium - Page 1:__", description=yokai_list_formated,  colour=0xf58f00)
                            Dropdown.message = await ctx.send(embed=main_embed, view=Dropdown)

                        #in case there is to many yo-kai, shouldn't be the case but who know? Edit: it's the case for nearly 100% medallium
                        except discord.errors.HTTPException:
                            error_embed = discord.Embed(color=discord.Color.red(),
                                                        title="Oh non, une erreur s'est produite !",
                                                        description="> Un bug sur cette commande se produit quand le Médallium est trop grand pour être affiché. (C'est un peu un flex quand même 🙃)")
                            error_embed.add_field(name="Vous devez donc spécifier un rang pour que cela marche.",
                                                value="Vous pouvez utiliser le message ci-dessus.")
                            return await interaction.response.send_message(embed=error_embed)

                else:
                    asked_class = await Cf.classid_to_class(self.values[0], True)
                    yokai_list_brute = yokai_per_class[asked_class]
                    classes_name = await Cf.classid_to_class(asked_class, False)
                    class_id = asked_class

                    yokai_list_formated = ""

                    if yokai_list_brute != {}:
                        for elements in yokai_list_brute:
                            if yokai_list_brute[elements] > 1:
                                yokai_list_formated += f"> {elements} **(x{str(yokai_list_brute[elements])})**\n"
                            else:
                                yokai_list_formated += f"> {elements}\n"

                        inv_embed = discord.Embed(
                            title=f"Yo-kai de Rang {classes_name} `{brute_inventory[class_id]}/{list_len[class_id]}`",
                            description=yokai_list_formated,
                            color=discord.Color.from_str(yokai_data[class_id]["color"])
                        )
                        inv_embed.set_thumbnail(url=image_link[class_id])
                        inv_embed.set_author(name=f"Médallium de {user.name}")
                        return await interaction.response.send_message(embed=inv_embed)
                    else:
                        if user.id == ctx.author.id:
                            inv_embed = discord.Embed(
                                title="Oops, votre Médallium ne contient pas de Yo-kai de ce rang 😢!")
                        else:
                            inv_embed = discord.Embed(
                                title=f"Oops, le Médallium de {user.name} ne contient pas de Yo-kai de ce rang 😢!")
                        return await interaction.response.send_message(embed=inv_embed)


        class Inv_dropdown_view(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)
                self.add_item(Inv_dropdown())
                
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit( embed=self.message.embeds[0], view=self)
                except discord.NotFound:
                    pass

        Dropdown = Inv_dropdown_view()

        #Create the main embed
        main_embed = discord.Embed(title="__Médallium -- Menu.__", colour=0xf58f00)

        #Make the nerdy stats :
        
        #the total and the actual for the completion of the medallium
        total = 0
        actual = 0
        total_point = 0
        
        yokai_claimed_count = ""
        for classes in yokai_per_class:     
            total += list_len[classes]
            
            actual += brute_inventory[classes]
            total_point += brute_inventory[classes]*data.class_to_point[classes]
            
            if brute_inventory[classes] == 0:
                pass
            elif len(classes) == 1:
                yokai_claimed_count += f"Yo-kai de rang **{await Cf.classid_to_class(classes, False)}**: `{brute_inventory[classes]}/{list_len[classes]}`\n"
            else:
                yokai_claimed_count += f"Yo-kai **{await Cf.classid_to_class(classes, False)}**: `{brute_inventory[classes]}/{list_len[classes]}`\n"
                
        #process the completion of the medallium
        completion = actual/total*100
        completion = round(completion, 2)

        main_embed.add_field(name="Voici vos statistiques :", value=yokai_claimed_count, inline=False)
        main_embed.add_field(name="Pourcentage et points:", value=f"> Médallium complété à **{completion}%** !\n> Votre Médallium vaut {total_point} points !\n-# faites /stats pour plus d'info sur les points.")
        if not user == None and user.id != ctx.author.id:
            main_embed.set_footer(text=f"Merci de choisir parmi les propositions ci-dessous pour afficher les Yo-kai de {user.display_name}.")
        
        else:
            main_embed.set_footer(text="Merci de choisir parmi les propositions ci-dessous pour afficher vos Yo-kai.")

        Dropdown.message = await ctx.send(embed=main_embed, view=Dropdown)

        if user.id == ctx.author.id:
            bag = await Cf.get_bag(user.id)
            bag["trophe_data"]["data"]["medallium completion"] = completion
            await Cf.trophe_check(user.id)

    
    #the bag command
    @commands.hybrid_command(name="bag")
    async def bag(self, ctx = commands.Context, user : discord.User = None ):
        """
        Permet de voir votre sacoche, tous les objets / pièces que vous avez eu avec le /bingo-kai. 
        Utilisez */bag {user}* pour voir la sacoche d'un autre utilisateur.
        """
        #define the user
        if user == None:
            user = ctx.author

        #Get bag
        brute_bag = await Cf.get_bag(user.id)

        #try if the bag is empty
        if brute_bag == {}:
            if user.id == ctx.author.id:
                inv_embed = discord.Embed(title="Oops, votre sacoche est vide 😢!")
            else:
                inv_embed = discord.Embed(title=f"Oops, la sacoche de {user.name} est vide 😢!")
            return await ctx.send(embed=inv_embed)

        #create the list :  
        item_per_class = {
            "coin": {},
            "obj": {},
            "treasure": {},
        }

        #sort the content by categorie
        for elements in brute_bag:
            #Don't take any numbers
            if not elements in ["coin", "obj", "treasure", "equipped_treasure", "last_daily_reset", "amount", "daily_shop_data", "trophe_data"]:
                categorie = brute_bag[elements]

                #Check if it's stack
                try:
                    count = brute_bag[elements][1]
                except:
                    count = 1

                #add it to the right list
                item_per_class[categorie[0]][elements] = count

        #sort the list alphabeticaly :
        for non_sorted_dicts in item_per_class:
            list_key = list(item_per_class[non_sorted_dicts].keys())
            list_key.sort()

            sorted_dict = {i: item_per_class[non_sorted_dicts][i] for i in list_key}
            item_per_class[non_sorted_dicts] = sorted_dict

        await Cf.update_trophe_data(ctx.author.id, "treasure", brute_bag["treasure"], "set")
        await Cf.update_trophe_data(ctx.author.id, "objects", brute_bag["obj"], "set")
        await Cf.trophe_check(ctx.author.id, ctx)

        #Inv dropdown class
        class Inv_dropdown(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label="Tout !", description="Affiche toute la sacoche.", emoji="🌐"),
                    discord.SelectOption(label="Pièces", emoji="🪙"),
                    discord.SelectOption(label="Objets", emoji="📦"),
                    discord.SelectOption(label="Trésors", emoji="📿"),
                ]

                super().__init__(placeholder='Choisissez ce que vous voulez...', min_values=1, max_values=1, options=options)

            async def callback(self, interaction, ctx=ctx):
                if self.values[0] == "Tout !":
                    if user.id == ctx.author.id:
                        inv_embed = discord.Embed(title="Voici votre sacoche :")
                    else:
                        inv_embed = discord.Embed(title=f"Voici le sacoche de {user.name} :")

                    try:
                        for classes in item_per_class:
                            item_list_brute = item_per_class[classes]
                            classes_name = await Cf.classid_to_class(classes, False)
                            class_id = classes

                            item_list_formated = ""

                            if item_list_brute != {}:
                                for elements in item_list_brute:
                                    if item_list_brute[elements] > 1:
                                        item_list_formated += f"> {elements} **`(x{str(item_list_brute[elements])})`**\n"
                                    else:
                                        item_list_formated += f"> {elements}\n"

                                inv_embed.add_field(name=f"{classes_name} `{brute_bag[class_id]}`",
                                                    value=item_list_formated)
                                inv_embed.set_author(name=f"Sacoche de {user.name}")
                        return await interaction.response.send_message(embed=inv_embed)
                    except discord.errors.HTTPException as e:
                        error_embed = discord.Embed(color=discord.Color.red(),
                                                    title="Oh non, une erreur s'est produite !",
                                                    description="> Un bug sur cette commande se produit quand la sacoche est trop grande pour être affichée. (C'est un peu un flex quand même 🙃)")
                        error_embed.add_field(name="Vous devez donc spécifier un type pour que cela marche.",
                                            value="Vous pouvez utiliser le message ci-dessus.")
                        return await interaction.response.send_message(embed=error_embed)

                else:
                    
                    if self.values[0] == "Pièces" :
                        item_type = "coin"
                        
                    elif self.values[0] == "Objets":
                        item_type = "obj"
                    
                    else :
                        item_type = "treasure"
                    
                    
                    
                    item_list_brute = item_per_class[item_type]
                    classes_name = self.values[0]
                    class_id = item_type

                    item_list_formated = ""

                    if item_list_brute != {}:
                        for elements in item_list_brute:
                            if item_list_brute[elements] > 1:
                                item_list_formated += f"> {elements} **`(x{str(item_list_brute[elements])})`**\n"
                            else:
                                item_list_formated += f"> {elements}\n"

                        inv_embed = discord.Embed(
                            title=f"{classes_name} `{brute_bag[item_type]}`",
                            description=item_list_formated,
                            color=discord.Color.from_str("#b87106")
                        )
                        
                        #NOT implented yet
                        #inv_embed.set_thumbnail(url=image_link[item_type])
                        
                        inv_embed.set_author(name=f"Sacoche de {user.name}")
                        return await interaction.response.send_message(embed=inv_embed)
                    else:
                        if user.id == ctx.author.id:
                            inv_embed = discord.Embed(
                                title="Oops, votre sacoche ne contient rien de ce type 😢!")
                        else:
                            inv_embed = discord.Embed(
                                title=f"Oops, la sacoche de {user.name} ne contient rien de ce type 😢!")
                        return await interaction.response.send_message(embed=inv_embed)


        class Inv_dropdown_view(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(Inv_dropdown())


        Dropdown = Inv_dropdown_view()

        #Create the main embed
        main_embed = discord.Embed(title="__Sacoche -- Menu.__", colour=discord.Colour.from_str("#b87106"))

        #Make the nerdy stats : 
        yokai_claimed_count = ""
        for classes in item_per_class:
            if brute_bag[classes] == 0:
                pass
            
            else:
                yokai_claimed_count += f"**{await Cf.classid_to_class(classes, False)}s**: `{brute_bag[classes]}`\n"


        main_embed.add_field(name="Voici vos statistiques :", value=yokai_claimed_count, inline=True)
        if not user == None and user.id != ctx.author.id:
            main_embed.set_footer(text=f"Merci de choisir parmi les propositions ci-dessous pour afficher les items de {user.display_name}.")
        
        else:
            main_embed.set_footer(text="Merci de choisir parmi les propositions ci-dessous pour afficher vos items.")


        await ctx.send(embed=main_embed, view=Dropdown)
        
    
    @commands.hybrid_command(name="stats")
    async def stats(self, ctx: commands.Context):
        """
        Donne des statistiques sur plein de choses !
        """
        #get what we need:
        drop_proba_formated = ""
        
        for i in range(12):
            drop_proba_formated += f"> **{await Cf.classid_to_class(data.class_list[i])}:** `{data.proba_list[i]*100}%`\n"
        
        point_formated = ""
        
        for c in data.class_list:
            point_formated += f"> **{await Cf.classid_to_class(c)}:** {data.class_to_point[c]} points\n"
            
        stats_embed = discord.Embed(title="__Voici les stats !__", color=discord.Color.from_str("#148A99"))
        
        stats_embed.add_field(name="__Taux de drop :__", value=drop_proba_formated.removesuffix("\n"))
        stats_embed.add_field(name="__Points par rang :__", value=point_formated.removesuffix("\n"))
        
        return await ctx.send(embed=stats_embed)
        

    @commands.hybrid_command(name="medallium_event")
    async def medallium_event(self, ctx = commands.Context, user : discord.User = None ):
        """
        Permet de voir votre médallium de yo-kai évènements!
        """


        #define the user
        if user == None:
            user = ctx.author

        #Get inventory
        brute_inventory = await Cf.get_inv(user.id)

        #try if the inv is empty
        if brute_inventory == {}:
            if user.id == ctx.author.id:
                inv_embed = discord.Embed(title="Oops, votre Médallium event est vide 😢!")
            else:
                inv_embed = discord.Embed(title=f"Oops, le Médallium event de {user.name} est vide 😢!")
            return await ctx.send(embed=inv_embed)

        #create the list :  
        yokai_per_class = {
            "Halloween": {},
            "Noël": {},
            "St-Valentin": {},
            "Printemps": {},
            "Pâques": {},
            "Estival": {},
            "Autre": {}
        }

        #sort the Yo-kai by class
        for elements in brute_inventory:
            if not type(brute_inventory[elements]) == int and not type(brute_inventory[elements]) == float:
            #Don't take any numbers
                try:
                    categorie = brute_inventory[elements][0]

                    #Check if it's stack
                    try:
                        count = brute_inventory[elements][1]
                    except:
                        count = 1

                    #add it to the right list
                    yokai_per_class[categorie][elements] = count
                except KeyError:
                    pass

        #sort the list alphabeticaly :
        for non_sorted_dicts in yokai_per_class:
            list_key = list(yokai_per_class[non_sorted_dicts].keys())
            list_key.sort()

            sorted_dict = {i: yokai_per_class[non_sorted_dicts][i] for i in list_key}
            yokai_per_class[non_sorted_dicts] = sorted_dict


        #define the emoji list
        emoji = data.emoji
        yokai_data = data.yokai_event_data
        list_len = data.event_list_len
        image_link = data.image_link




        #Inv dropdown class
        class Inv_dropdown(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label="Tout !", description="Affiche tout le Médallium event si possible.", emoji="🌐"),
                    discord.SelectOption(label="Halloween", emoji=emoji["Halloween"]),
                    discord.SelectOption(label="Noël", emoji=emoji["Noël"]),
                    discord.SelectOption(label="St-Valentin", emoji=emoji["St-Valentin"]),
                    discord.SelectOption(label="Printemps", emoji=emoji["Printemps"]),
                    discord.SelectOption(label="Pâques", emoji=emoji["Pâques"]),
                    discord.SelectOption(label="Estival", emoji=emoji["Estival"]),
                    discord.SelectOption(label="Autre", emoji=emoji["Autre"])
                ]

                super().__init__(placeholder='Choisissez le rang que vous voulez...', min_values=1, max_values=1, options=options)

            async def callback(self, interaction, ctx=ctx):
                if self.values[0] == "Tout !":
                    if user.id == ctx.author.id:
                        inv_embed = discord.Embed(title="Voici votre Médallium event :")
                    else:
                        inv_embed = discord.Embed(title=f"Voici le Médallium event de {user.name} :")

                    try:
                        for classes in yokai_per_class:
                            yokai_list_brute = yokai_per_class[classes]
                            classes_name = classes
                            class_id = classes

                            yokai_list_formated = ""

                            if yokai_list_brute != {}:
                                for elements in yokai_list_brute:
                                    if yokai_list_brute[elements] > 1:
                                        yokai_list_formated += f"> {elements} **`(x{str(yokai_list_brute[elements])})`**\n"
                                    else:
                                        yokai_list_formated += f"> {elements}\n"

                                inv_embed.add_field(name=f"Rang {classes_name} `{brute_inventory[class_id]}/{list_len[class_id]}`",
                                                    value=yokai_list_formated)
                                inv_embed.set_author(name=f"Médallium de {user.name}")
                        return await interaction.response.send_message(embed=inv_embed)
                    #if the medallium is to big to be in one message
                    except discord.errors.HTTPException as e:
                        error_embed = discord.Embed(color=discord.Color.red(),
                                                    title="Oh non, une erreur s'est produite !",
                                                    description="> Un bug sur cette commande se produit quand la sacoche est trop grande pour être affichée. (C'est un peu un flex quand même 🙃)")
                        error_embed.add_field(name="Vous devez donc spécifier un type pour que cela marche.",
                                            value="Vous pouvez utiliser le message ci-dessus.")
                        return await interaction.response.send_message(embed=error_embed)

                else:
                    asked_class = self.values[0]
                    classes = asked_class
                    yokai_list_brute = yokai_per_class[asked_class]
                    classes_name = asked_class
                    class_id = asked_class

                    yokai_list_formated = ""

                    if yokai_list_brute != {}:
                        for elements in yokai_list_brute:
                            if yokai_list_brute[elements] > 1:
                                yokai_list_formated += f"> {elements} **(x{str(yokai_list_brute[elements])})**\n"
                            else:
                                yokai_list_formated += f"> {elements}\n"

                        inv_embed = discord.Embed(
                            title=f"Yo-kai de Rang {classes_name} `{brute_inventory[class_id]}/{list_len[class_id]}`",
                            description=yokai_list_formated,
                            color=discord.Color.from_str(yokai_data[class_id]["color"])
                        )
                        #inv_embed.set_thumbnail(url=image_link[class_id])
                        inv_embed.set_author(name=f"Médallium de {user.name}")
                        return await interaction.response.send_message(embed=inv_embed)
                    else:
                        if user.id == ctx.author.id:
                            inv_embed = discord.Embed(
                                title="Oops, votre Médallium évènement ne contient pas de Yo-kai de ce rang 😢!")
                        else:
                            inv_embed = discord.Embed(
                                title=f"Oops, le Médallium évènement de {user.name} ne contient pas de Yo-kai de ce rang 😢!")
                        return await interaction.response.send_message(embed=inv_embed)


        class Inv_dropdown_view(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)
                self.add_item(Inv_dropdown())
                
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit( embed=self.message.embeds[0], view=self)
                except discord.NotFound:
                    pass

        Dropdown = Inv_dropdown_view()

        #Create the main embed
        main_embed = discord.Embed(title="__Médallium évènement -- Menu.__", colour=0xf58f00)

        #Make the nerdy stats :
        
        #the total and the actual for the completion of the medallium
        total = 0
        actual = 0
        total_point = 0
        
        yokai_claimed_count = ""
        for classes in yokai_per_class:     
            total += list_len[classes]
            
            actual += brute_inventory[classes]
            
            if brute_inventory[classes] == 0:
                pass
            elif len(classes) == 1:
                yokai_claimed_count += f"Yo-kai de rang **{classes}**: `{brute_inventory[classes]}/{list_len[classes]}`\n"
            else:
                yokai_claimed_count += f"Yo-kai **{classes}**: `{brute_inventory[classes]}/{list_len[classes]}`\n"
                
        #process the completion of the medallium
        completion = actual/total*100
        completion = round(completion, 2)

        main_embed.add_field(name="Voici vos statistiques :", value=yokai_claimed_count, inline=False)
        main_embed.add_field(name="Pourcentage de complétion:", value=f"> Médallium complété à **{completion}%** !\n-# faites /stats pour plus d'info sur les points.")
        if not user == None and user.id != ctx.author.id:
            main_embed.set_footer(text=f"Merci de choisir parmi les propositions ci-dessous pour afficher les Yo-kai de {user.display_name}.")
        
        else:
            main_embed.set_footer(text="Merci de choisir parmi les propositions ci-dessous pour afficher vos Yo-kai.")

        Dropdown.message = await ctx.send(embed=main_embed, view=Dropdown)


    #the commande to see all yours trophes
    @commands.hybrid_command(name="trophe")
    async def trophe(self, ctx = commands.Context, user : discord.User = None):
        """
        New ✨ ! Permet de voir la liste des trophées!
        """
        if user == None:
            user = ctx.author
        
        bag = await Cf.get_bag(user.id)

        class Inv_dropdown(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label="Tout !", description="Affiche tout les trophées.", emoji="🌐"),
                    discord.SelectOption(label="medallium", description="Affiche tout les trophées de la catégorie médallium.", emoji="🌐"),
                    discord.SelectOption(label="cadeau", description="Affiche tout les trophées de la catégorie cadeau.", emoji="🎁"),
                    discord.SelectOption(label="trade", description="Affiche tout les trophées de la catégorie trade.", emoji="🌐"),
                    discord.SelectOption(label="fusion", description="Affiche tout les trophées de la catégorie fusion.", emoji="🌐"),
                    discord.SelectOption(label="top", description="Affiche tout les trophées de la catégorie top.", emoji="🌐"),
                    discord.SelectOption(label="shop", description="Affiche tout les trophées de la catégorie shop.", emoji="🌐"),
                    discord.SelectOption(label="terrheure", description="Affiche tout les trophées de la catégorie terrheure.", emoji="🌐"),
                    discord.SelectOption(label="bag", description="Affiche tout les trophées de la catégorie bag.", emoji="🌐"),
                    discord.SelectOption(label="orbes", description="Affiche tout les trophées de la catégorie orbes.", emoji="🌐"),
                    discord.SelectOption(label="search", description="Affiche tout les trophées de la catégorie search.", emoji="🌐"),
                    discord.SelectOption(label="bingo-kai", description="Affiche tout les trophées de la catégorie bingo-kai.", emoji="🌐")
                ]

                super().__init__(placeholder='Choisissez la catégorie que vous voulez...', min_values=1, max_values=1, options=options)

            async def callback(self, interaction, ctx=ctx):
                if self.values[0] == "Tout !":
                    trophe_list = ""

                    for trophe in data.trophe_data:
                        if trophe in bag["trophe_data"]["list"]:
                            trophe_list += (f"🏆**{trophe}** ✅\nObtention: {data.trophe_data[trophe]["obtention"]}\n\n")

                        else:
                            trophe_list += (f"🏆**{trophe}** ❌\nObtention: {data.trophe_data[trophe]["obtention"]}\n\n")

                    trophe_embed = discord.Embed(
                                title = f"Liste des trophées de {user.name}",
                                description = trophe_list,
                                color = discord.colour.Color.yellow()
                            )
                else:
                    trophe_list = ""

                    for trophe in data.trophe_data:
                        if data.trophe_data[trophe]["categorie"] == self.values[0]:
                            if trophe in bag["trophe_data"]["list"]:
                                trophe_list += (f"{data.emoji[data.trophe_data[trophe]["type"]]} **{trophe}** ✅\nObtention: {data.trophe_data[trophe]["obtention"]}\n\n")
                            
                            else:
                                trophe_list += (f"{data.emoji[data.trophe_data[trophe]["type"]]} **{trophe}** ❌\nObtention: {data.trophe_data[trophe]["obtention"]}\n\n")

                    trophe_embed = discord.Embed(
                        title = f"Liste des trophées de {user.name} dans la catégorie {self.values[0]}:",
                        description = trophe_list,
                        color = discord.colour.Color.yellow()
                    )
                return await interaction.response.send_message(embed=trophe_embed)
                
        class Inv_dropdown_view(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)
                self.add_item(Inv_dropdown())
                
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit( embed=self.message.embeds[0], view=self)
                except discord.NotFound:
                    pass

        Dropdown = Inv_dropdown_view()

        #Create the main embed
        main_embed = discord.Embed(title="__Trophées -- Menu.__", colour=0xf58f00)

        main_embed.add_field(name="Voici vos statistiques :", value= f"Vous avez {len(bag["trophe_data"]["list"])} / 56 trophées.", inline=False)
        if not user == None and user.id != ctx.author.id:
            main_embed.set_footer(text=f"Merci de choisir parmi les propositions ci-dessous pour afficher les trophées de {user.display_name}.")
        
        else:
            main_embed.set_footer(text="Merci de choisir parmi les propositions ci-dessous pour afficher vos trophées.")

        Dropdown.message = await ctx.send(embed=main_embed, view=Dropdown)



async def setup(bot) -> None:
    await bot.add_cog(Medallium(bot))
