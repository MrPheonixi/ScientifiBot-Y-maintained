import os
import discord
import bot_package.data as data
import bot_package.Custom_func as cf
from PIL import Image, UnidentifiedImageError, ImageDraw
from datetime import datetime
import requests
import random
import asyncio
import io


SONDAGE_PATH = "./files/sondage.json"


class SondageView(discord.ui.View):
    def __init__(self, sondage_data_path: str, user_id: int, choice1: str, choice2: str):
        super().__init__(timeout=30)
        self.sondage_data_path = sondage_data_path
        self.user_id = user_id
        self.choice1 = choice1
        self.choice2 = choice2
        self.voted = False
        self.message = None  # sera assigné juste après l'envoi du message

        # Renomme dynamiquement les boutons avec les noms des yokai
        self.children[0].label = choice1
        self.children[1].label = choice2

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Empêche quelqu'un d'autre de voter à ta place (sécurité, même si le message est éphémère)
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Ce sondage n'est pas pour toi !", ephemeral=True)
            return False
        return True

    async def _register_vote(self, interaction: discord.Interaction, choice_num: int):
        self.voted = True
        sondage_data = data.open_json(self.sondage_data_path)

        if choice_num == 1:
            sondage_data["choice1"] += 1
        else:
            sondage_data["choice2"] += 1

        today_users = sondage_data.setdefault("today_user", [])
        if str(self.user_id) not in today_users:
            today_users.append(str(self.user_id))

        data.save_json(self.sondage_data_path, sondage_data)

        for child in self.children:
            child.disabled = True

        winner_label = self.choice1 if choice_num == 1 else self.choice2
        await interaction.response.edit_message(
            content=f"✅ Merci pour ton vote pour **{winner_label}** !",
            embed=None,
            view=self
        )
        self.stop()

    @discord.ui.button(label="Choix 1", style=discord.ButtonStyle.primary)
    async def choice1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._register_vote(interaction, 1)

    @discord.ui.button(label="Choix 2", style=discord.ButtonStyle.primary)
    async def choice2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._register_vote(interaction, 2)

    async def on_timeout(self):
        if not self.voted:
            for child in self.children:
                child.disabled = True
            if self.message is not None:
                try:
                    await self.message.edit(
                        content="⏱️ Temps écoulé, aucun choix. Tu pourras revoter à ton prochain bingo-kai.",
                        view=self
                    )
                except (discord.NotFound, discord.HTTPException):
                    pass


class sondage():
    def __init__(self, bot=None):
        self.bot = bot

    def _get_image_from_url(self, url, size=(512, 512)):
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            image.load()
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            if image.size != size:
                image = image.resize(size)
            return image
        except (requests.RequestException, OSError, UnidentifiedImageError, ValueError):
            return Image.new("RGBA", size, (0, 0, 0, 0))

    def _get_image_from_path(self, path, size=(512, 512)):
        if not path or not os.path.exists(path):
            return Image.new("RGBA", size, (0, 0, 0, 0))
        try:
            with Image.open(path) as image:
                image.load()
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                if image.size != size:
                    image = image.resize(size)
                return image
        except (FileNotFoundError, OSError, UnidentifiedImageError, ValueError):
            return Image.new("RGBA", size, (0, 0, 0, 0))

    async def sondage(self, ctx, user_id):
        # get the sondage data
        sondage_data = data.open_json(SONDAGE_PATH)
        cs = sondage_data["current_stage"]
        stage_key = str(cs)
        next_stage_key = str(cs + 1)
        need_reset = False
        # get the last day of poll
        last_day = sondage_data["last_day"]
        # get the current day
        current_day = datetime.now().strftime("%Y-%m-%d")
        if last_day != current_day:
            sondage_data["last_day"] = current_day
            need_reset = True
        if need_reset:
            # post the result of the poll in the poll channel if configured
            # prefer environment variable POLL_CHANNEL_LINK, fallback to config
            poll_channel = None
            env_link = os.getenv("POLL_CHANNEL_LINK") or data.config_data.get("poll_channel_id")
            channel_id = None
            if env_link:
                try:
                    if isinstance(env_link, str) and "/channels/" in env_link:
                        channel_id = int(env_link.rstrip("/").split("/")[-1])
                    else:
                        channel_id = int(env_link)
                except Exception:
                    channel_id = None
            if channel_id:
                poll_channel = self.bot.get_channel(channel_id)
                if poll_channel is None:
                    try:
                        poll_channel = await self.bot.fetch_channel(channel_id)
                    except Exception:
                        poll_channel = None
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

            # crée la liste suivante si non existante
            next_stage_list = sondage_data.setdefault(next_stage_key, [])
            # mettre le gagnant dans la list
            next_stage_list.append(sondage_data["last_selection1"])
            current_stage_list = sondage_data.setdefault(stage_key, [])
            # si il reste que un yk dans la current list, le faire passer ainsi que le notifier
            if len(current_stage_list) == 1:
                next_stage_list.append(current_stage_list[0])
                poll_embed.add_field(name=f"le tour numéro {cs} est fini!", value=f"de manière exceptionnelle, le yokai {current_stage_list[0]} est passé au tour suivant car il était le dernier restant dans la liste!")
                sondage_data[stage_key] = []
            if len(current_stage_list) == 0:
                sondage_data["current_stage"] += 1
                poll_embed.add_field(name=f"le tour numéro {cs} est fini!", value=f"Le stage {cs} est terminé, le tour n°{cs+1} commence !")
            last_day_img_path = f"./files/poll_image/{last_day}.png"
            if os.path.exists(last_day_img_path):
                last_day_img = self._get_image_from_path(last_day_img_path)
                if last_day_img.size != (0, 0):
                    poll_embed.set_image(url=f"attachment://{os.path.basename(last_day_img_path)}")
                    if poll_channel is not None:
                        await poll_channel.send(embed=poll_embed, file=discord.File(last_day_img_path, filename=os.path.basename(last_day_img_path)))
                    else:
                        await ctx.send(embed=poll_embed)
                else:
                    if poll_channel is not None:
                        await poll_channel.send(embed=poll_embed)
                    else:
                        await ctx.send(embed=poll_embed)
            else:
                if poll_channel is not None:
                    await poll_channel.send(embed=poll_embed)
                else:
                    await ctx.send(embed=poll_embed)
            # reset the poll data for the new day
            sondage_data["last_day"] = current_day
            sondage_data["choice1"] = 0
            sondage_data["choice2"] = 0
            sondage_data["today_user"] = []
            # choose 2 new yokai and make other stuff
            current_stage_list = sondage_data.setdefault(stage_key, [])
            if len(current_stage_list) >= 2:
                yk1 = random.choice(current_stage_list)
                current_stage_list.remove(yk1)
                yk2 = random.choice(current_stage_list)
                current_stage_list.remove(yk2)
            else:
                yk1 = current_stage_list[0] if current_stage_list else sondage_data.get("last_selection1") or "?"
                yk2 = current_stage_list[1] if len(current_stage_list) > 1 else sondage_data.get("last_selection2") or "?"
            sondage_data["last_selection1"] = yk1
            sondage_data["last_selection2"] = yk2

            # create the poll image
            id_list = data.yokai_list_full
            id1 = id_list.get(yk1, {}).get("id")
            id2 = id_list.get(yk2, {}).get("id")
            if id1 and id2:
                imgyk1 = self._get_image_from_url(f"https://slimepunk.fr/bello/sby/{id1}.png")
                imgyk2 = self._get_image_from_url(f"https://slimepunk.fr/bello/sby/{id2}.png")
            else:
                imgyk1 = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
                imgyk2 = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        else:
            yk1 = sondage_data.get("last_selection1")
            yk2 = sondage_data.get("last_selection2")
            id_list = data.yokai_list_full
            id1 = id_list.get(yk1, {}).get("id")
            id2 = id_list.get(yk2, {}).get("id")
            if id1 and id2:
                imgyk1 = self._get_image_from_url(f"https://slimepunk.fr/bello/sby/{id1}.png")
                imgyk2 = self._get_image_from_url(f"https://slimepunk.fr/bello/sby/{id2}.png")
            else:
                imgyk1 = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
                imgyk2 = Image.new("RGBA", (512, 512), (0, 0, 0, 0))

        # If fetched yokai images are empty (transparent), replace with a visible placeholder
        try:
            if imgyk1.getbbox() is None:
                imgyk1 = Image.new("RGBA", (512, 512), (80, 80, 80, 255))
            if imgyk2.getbbox() is None:
                imgyk2 = Image.new("RGBA", (512, 512), (80, 80, 80, 255))
        except Exception:
            # if something unexpected, ensure images are valid
            imgyk1 = imgyk1 if isinstance(imgyk1, Image.Image) else Image.new("RGBA", (512, 512), (80, 80, 80, 255))
            imgyk2 = imgyk2 if isinstance(imgyk2, Image.Image) else Image.new("RGBA", (512, 512), (80, 80, 80, 255))

        os.makedirs("./files/poll_image", exist_ok=True)
        im = Image.new("RGBA", (1024, 512), (0, 0, 0, 0))
        im.paste(imgyk1, (0, 0))
        im.paste(imgyk2, (512, 0))
        vs_image = self._get_image_from_path("./files/poll_image/vs.png")
        if vs_image.size == (512, 512):
            im.paste(vs_image, (256, 0), vs_image)
        image_path = f"./files/poll_image/{current_day}.png"
        im.save(image_path)
        data.save_json(SONDAGE_PATH, sondage_data)

        # Vérifie si l'utilisateur a déjà voté aujourd'hui
        today_users = sondage_data.get("today_user", [])
        if str(user_id) in today_users:
            return

        # Prépare l'embed et la vue avec boutons
        poll_embed = discord.Embed(
            title="Sondage du jour !",
            description=f"Vote pour ton yokai préféré !\n\n{sondage_data['last_selection1']} ou {sondage_data['last_selection2']} ?",
            color=discord.Color.blue()
        )
        poll_embed.set_image(url=f"attachment://{os.path.basename(image_path)}")

        view = SondageView(
            SONDAGE_PATH,
            user_id,
            sondage_data["last_selection1"],
            sondage_data["last_selection2"]
        )

        await ctx.send(
            embed=poll_embed,
            file=discord.File(image_path, filename=os.path.basename(image_path)),
            view=view,
            ephemeral=True
        )

        # Récupère le message réel pour permettre l'édition au timeout (on_timeout)
        try:
            if getattr(ctx, "interaction", None) is not None:
                view.message = await ctx.interaction.original_response()
        except (discord.NotFound, discord.HTTPException, AttributeError):
            view.message = None