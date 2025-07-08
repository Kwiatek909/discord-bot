import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional
from datetime import datetime, timezone
import random

def hex_color(hex_str):
    # Poprawka: discord.Color oczekuje int, więc bezpośrednio zwracamy int
    return discord.Color(int(hex_str.lstrip('#'), 16))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Potrzebne do pobierania ról użytkownika

bot = commands.Bot(command_prefix=';', intents=intents, help_command=None)
tree = bot.tree
    
@bot.event
async def on_ready():
    await tree.sync()
    print(f'{bot.user} jest online!')
    activity = discord.Activity(type=discord.ActivityType.listening, name="/pomoc")
    await bot.change_presence(activity=activity)
    
@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Ping poprawny {latency} ms")
    
@bot.command(name='msg')
async def msg(ctx, *, message_content: str):
    if not ctx.author.guild_permissions.administrator:
        print(f"Użytkownik {ctx.author} (ID: {ctx.author.id}) próbował użyć komendy '{ctx.command.name}', ale nie posiada uprawnień administratora.")
        return 

    await ctx.send(message_content)
    await ctx.message.delete()
    
@tree.command(name="pomoc", description="Wyświetla kartę pomocy bota")
async def pomoc_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Pomoc",
        description=(
            "Oto karta pomocy bota!\n"
            "Ostatnimi dniami hosting bota miał problemy i musieliśmy go zmienić.\n"
            "W dalszym ciągu odbudowujemy komendy i wszystkie funkcje jakie miała stara wersja bota.\n"
            "Niektóre funkcje mogą działać trochę inaczej.\n"
            "Za wszelkie problemy przepraszamy!\n\n"
            "**Komendy**\n"
            "`Prefix - ;`\n"
            "ping - pokazuje opóźnienie bota i sprawdza jego aktywność\n"
            "wnioski - wysyła zbiór wniosków które można wysłać (tylko admin)\n"
            "msg - bot wyśle wiadomość jaką będziesz chciał (tylko admin)\n\n"
            "`Ukośnik - /`\n"
            "pomoc - wyświetla kartę pomocy bota\n"
            "twitter - pozwala opublikować posta na kanale <#1282096776928559246>\n"
            "news - pozwala opublikować posta na kanale <#1228665355832922173> (tylko admin)\n"
            "rejestracja - udostępnia wynik rejestracji (tylko admin)\n"
            "kontrakt - wysyła kontrakt do FIA\n"
        ),
        color=hex_color("#FFFFFF")
    )

    if interaction.guild and interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text="Official Polish Racing Fortnite")

    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- MODAL: Regulamin ---
class RegulaminModal(discord.ui.Modal, title="Regulacja"):
    zmiana = discord.ui.TextInput(
        label="Jaką regulację byś zmienił lub dodał?",
        placeholder="Np. Zmiana limitu okrążeń...",
        min_length=5,
        max_length=100
    )
    powod = discord.ui.TextInput(
        label="Powód",
        placeholder="Np. obecna regulacja jest zbyt surowa",
        min_length=5,
        max_length=100
    )
    uzasadnienie = discord.ui.TextInput(
        label="Uzasadnienie",
        style=discord.TextStyle.paragraph,
        placeholder="Opisz dokładnie swoje zdanie (max 500 znaków)",
        min_length=10,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Regulacja",
            color=hex_color("#FFA500")
        )
        embed.add_field(name="Jaką regulację byś zmienił lub dodał?", value=self.zmiana.value, inline=False)
        embed.add_field(name="Powód", value=self.powod.value, inline=False)
        embed.add_field(name="Uzasadnienie", value=self.uzasadnienie.value, inline=False)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/800px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png")
        embed.set_footer(text="Official Polish Racing Fortnite")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message("Twoja regulacja została wysłana!", ephemeral=True)

        KANAL_ID = 1284911511583719558  # <-- zamień na swój kanał docelowy

        kanal_docelowy = interaction.guild.get_channel(KANAL_ID)
        if kanal_docelowy:
            await kanal_docelowy.send(embed=embed)

    
# --- MODAL: Skład ---
class SkladModal(discord.ui.Modal, title="Zgłoś skład"):
    kierowcy = discord.ui.TextInput(
        label="Kierowcy",
        placeholder="Kamil #32, Niko #66",
        min_length=5,
        max_length=100
    )
    akademia = discord.ui.TextInput(
        label="Akademia",
        placeholder="Red Bull",
        min_length=2,
        max_length=50
    )
    grand_prix = discord.ui.TextInput(
        label="Grand Prix",
        placeholder="S3-R5-GP Japonii",
        min_length=5,
        max_length=50
    )
    dywizja = discord.ui.TextInput(
        label="Dywizja",
        placeholder="F1",
        min_length=2,
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Zgłoszony skład",
            color=hex_color("#FFA500")
        )
        embed.add_field(name="Kierowcy", value=self.kierowcy.value, inline=False)
        embed.add_field(name="Akademia", value=self.akademia.value, inline=False)
        embed.add_field(name="Grand Prix", value=self.grand_prix.value, inline=False)
        embed.add_field(name="Dywizja", value=self.dywizja.value, inline=False)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/800px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png")
        embed.set_footer(text="Official Polish Racing Fortnite")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message("Zgłoszenie składu zostało wysłane!", ephemeral=True)

        # 🔁 TUTAJ PODAJ ID kanału, do którego ma zostać wysłany embed
        KANAL_ID = 1284911511583719558  # <--- ZAMIEŃ NA PRAWDZIWE ID KANAŁU

        kanal_docelowy = interaction.guild.get_channel(KANAL_ID)
        if kanal_docelowy:
            await kanal_docelowy.send(embed=embed)


# --- MODAL: Odwołanie od kary ---
class OdwolanieModal(discord.ui.Modal, title="Odwołanie od kary"):
    kierowca = discord.ui.TextInput(
        label="Dane Kierowcy",
        placeholder="Makłini #95",
        min_length=5,
        max_length=40
    )
    grand_prix = discord.ui.TextInput(
        label="Grand Prix",
        placeholder="S3-R5-GP Japonii",
        min_length=5,
        max_length=50
    )
    zamieszani = discord.ui.TextInput(
        label="Zamieszani",
        placeholder="Kamil #32, Niko #66",
        min_length=5,
        max_length=50
    )
    tresc = discord.ui.TextInput(
        label="Treść",
        placeholder="Szanowne FIA, Witam was serdecznie...",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Odwołanie od kary",
            color=hex_color("#FFA500")
        )
        embed.add_field(name="Dane Kierowcy", value=self.kierowca.value, inline=False)
        embed.add_field(name="Grand Prix", value=self.grand_prix.value, inline=False)
        embed.add_field(name="Zamieszani", value=self.zamieszani.value, inline=False)
        embed.add_field(name="Treść", value=self.tresc.value, inline=False)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/800px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png")
        embed.set_footer(text="Official Polish Racing Fortnite")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message("Twoje odwołanie zostało złożone!", ephemeral=True)

        # 🔁 TUTAJ PODAJ ID kanału, do którego ma zostać wysłany embed
        KANAL_ID = 1284911511583719558  # <--- ZAMIEŃ NA PRAWDZIWE ID KANAŁU

        kanal_docelowy = interaction.guild.get_channel(KANAL_ID)
        if kanal_docelowy:
            await kanal_docelowy.send(embed=embed)
        else:
            await interaction.followup.send("Nie znaleziono kanału docelowego!", ephemeral=True)

# --- VIEW: Wnioski ---
class WnioskiView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Odwołanie od kary", emoji="📩", style=discord.ButtonStyle.success, custom_id="wniosek_odwolanie")
    async def odwolanie_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OdwolanieModal())

    @discord.ui.button(label="Regulamin", emoji="📩", style=discord.ButtonStyle.success, custom_id="wniosek_regulamin")
    async def regulamin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegulaminModal())

    @discord.ui.button(label="Zgłoś skład", emoji="📩", style=discord.ButtonStyle.success, custom_id="wniosek_sklad")
    async def sklad_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SkladModal())
        
# --- KOMENDA: Wnioski ---
@bot.command(name='wnioski')
@commands.has_permissions(administrator=True)
async def wnioski(ctx):
    embed = discord.Embed(
        title="Wnioski",
        description=(
            "Napisz oficjalny wniosek do FIA.\n"
            "Pamiętaj o wymogach podczas pisania.\n"
            "Klikając przycisk, wyświetli ci się okienko,\n"
            "w którym będziesz mógł stworzyć wniosek.\n"
            "Stosuj się do przykładów."
        ),
        color=hex_color("#FF8C00")
    )
    embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/800px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png")
    embed.set_footer(text="Official Polish Racing Fortnite")

    await ctx.send(embed=embed, view=WnioskiView())
    await ctx.message.delete()
    
# --- MODALE TWEETER I NEWS ---
class TwitterModal(discord.ui.Modal, title="Twitter"):
    tytul = discord.ui.TextInput(label="Tytuł", min_length=3, max_length=50)
    tresc = discord.ui.TextInput(label="Treść", style=discord.TextStyle.paragraph, min_length=10, max_length=4000)

    def __init__(self, image: Optional[discord.Attachment]):
        super().__init__()
        self.image = image

    async def on_submit(self, interaction_modal: discord.Interaction):
        user = interaction_modal.user
        avatar_url = user.display_avatar.url
        username = user.name

        embed = discord.Embed(
            title=self.tytul.value,
            description=self.tresc.value,
            color=hex_color("#0ff5ed")
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1281938731175247955.webp?size=80")
        embed.set_author(name=username, icon_url=avatar_url)
        embed.set_footer(text="Wysłano")
        embed.timestamp = datetime.now(timezone.utc)

        if self.image and self.image.content_type.startswith("image"):
            embed.set_image(url=self.image.url)

        kanal = interaction_modal.guild.get_channel(1282096776928559246)
        if kanal:
            msg = await kanal.send(embed=embed)
            await msg.add_reaction("❤️")
            await interaction_modal.response.send_message("Pomyślnie opublikowano posta!", ephemeral=True)
        else:
            await interaction_modal.response.send_message("Nie znaleziono kanału docelowego!", ephemeral=True)

# Przeniesiona definicja NewsModal na zewnątrz news_command, aby była globalnie dostępna
class NewsModal(discord.ui.Modal, title="Nowy News"): 
    tytul = discord.ui.TextInput(label="Tytuł", style=discord.TextStyle.short, required=True, min_length=3, max_length=50)
    tresc = discord.ui.TextInput(label="Treść", style=discord.TextStyle.paragraph, required=True, min_length=10, max_length=4000)

    # Zmodyfikowany __init__ aby przyjmował role_id i bot_reactions
    def __init__(self, image: Optional[discord.Attachment], role_id: int, bot_reactions: list):
        super().__init__()
        self.image = image
        self.role_id = role_id
        self.bot_reactions = bot_reactions

    async def on_submit(self, interaction_modal: discord.Interaction):
        user = interaction_modal.user
        avatar_url = user.display_avatar.url
        username = user.name

        embed = discord.Embed(
            title=self.tytul.value,
            description=self.tresc.value,
            color=hex_color("#FFFFFF")
        )
        embed.set_author(name=username, icon_url=avatar_url)
        embed.set_footer(text="Wysłano")
        embed.timestamp = datetime.now(timezone.utc)

        if self.image and self.image.content_type.startswith("image"):
            embed.set_image(url=self.image.url)

        kanal = interaction_modal.guild.get_channel(1228665355832922173) # Kanał docelowy dla newsów
        if kanal:
            # Pobieranie obiektu roli do wzmianki
            role_to_mention = interaction_modal.guild.get_role(self.role_id)
            content_message = ""
            if role_to_mention:
                content_message = f"{role_to_mention.mention}\n" # Wzmianka roli nad embedem

            # Wysyłanie wiadomości z wzmianką roli i embedem
            msg = await kanal.send(content=content_message, embed=embed)
            
            # Dodawanie reakcji bota
            for emoji in self.bot_reactions:
                try:
                    await msg.add_reaction(emoji)
                except discord.HTTPException as e:
                    print(f"Nie udało się dodać reakcji {emoji}: {e}")

            await interaction_modal.response.send_message("Pomyślnie opublikowano newsa!", ephemeral=True)
        else:
            await interaction_modal.response.send_message("Nie znaleziono kanału docelowego dla newsa!", ephemeral=True)


# --- KOMENDY ---
@tree.command(name="kontrakt", description="Wyślij kontrakt do FIA!")
@app_commands.describe(kierowca="kierowca", zespol="zespol", kontrakt="plik kontraktu")
async def kontrakt_command(interaction: discord.Interaction, kierowca: discord.User, zespol: discord.Role, kontrakt: discord.Attachment):
    szef_id = interaction.user.id
    kanal = interaction.guild.get_channel(1246088962649362542)
    if kanal:
        await kanal.send(f"Szef Zespołu: <@{szef_id}>\nKierowca: {kierowca.mention}\nZespół: {zespol.mention}\n{kontrakt.url}")
    await interaction.response.send_message("Pomyślnie wysłano kontrakt do FIA!", ephemeral=True)
    
@tree.command(name="racecontrol", description="Wyślij powiadomienie Race Control!")
@app_commands.describe(
    typ="Typ powiadomienia",
    powod="Powód wydania powiadomienia", 
    pojazd="Kierowca/Pojazd #1",
    opis="Szczegółowy opis sytuacji",
    pojazd2="Kierowca/Pojazd #2 (opcjonalnie)",
    pojazd3="Kierowca/Pojazd #3 (opcjonalnie)"
)
async def racecontrol_command(
    interaction: discord.Interaction, 
    typ: str, 
    powod: str, 
    pojazd: discord.User, 
    opis: str,
    pojazd2: discord.User = None,
    pojazd3: discord.User = None
):
    # Sprawdzenie uprawnień
    required_role_id = 1188129655153242172
    if not any(role.id == required_role_id for role in interaction.user.roles):
        await interaction.response.send_message("Nie masz uprawnień do używania tej komendy!", ephemeral=True)
        return
    
    # Pobranie kanału
    kanal = interaction.guild.get_channel(1222890220584697957)
    if not kanal:
        await interaction.response.send_message("Nie znaleziono kanału docelowego!", ephemeral=True)
        return
    
    # Budowanie listy pojazdów
    pojazdy_list = [pojazd.mention]
    if pojazd2:
        pojazdy_list.append(pojazd2.mention)
    if pojazd3:
        pojazdy_list.append(pojazd3.mention)
    pojazdy_text = ", ".join(pojazdy_list)
    
    # Ustawienie koloru i thumbnail w zależności od typu
    if typ.lower() == "normal":
        embed_color = 0x063672  # Niebieski
        thumbnail_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/1200px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png"
    elif typ.lower() == "dochodzenie":
        embed_color = 0xff8000  # Pomarańczowy
        thumbnail_url = "https://cdn.discordapp.com/emojis/1237437135645315184.webp?size=96"
    else:
        embed_color = 0x063672  # Domyślny niebieski
        thumbnail_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/1200px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png"
    
    # Pobieranie aktualnej godziny dla strefy czasowej polskiej
    import datetime
    teraz = datetime.datetime.now()
    # Dodanie 2 godzin dla czasu polskiego (CET/CEST)
    teraz_polska = teraz + datetime.timedelta(hours=2)
    czas = teraz_polska.strftime("%H:%M")
    
    # Tworzenie embed
    embed = discord.Embed(
        title="**Race Control - Powiadomienie**",
        color=embed_color
    )
    
    # Ustawienie author z logo FIA
    embed.set_author(
        name="Fédération Internationale de l'Automobile",
        icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/1200px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png"
    )
    
    # Ustawienie thumbnail
    embed.set_thumbnail(url=thumbnail_url)
    
    # Dodanie pól
    embed.add_field(name="**Race Control:**", value=powod, inline=True)
    embed.add_field(name="**Czas:**", value=czas, inline=True)
    embed.add_field(name="**Pojazdy:**", value=pojazdy_text, inline=False)
    embed.add_field(name="**Powód:**", value=opis, inline=False)
    
    # Wysłanie embed
    ID_ROLI_RACE_CONTROL_PING = 1285222412513710171
    await kanal.send(f"<@&{ID_ROLI_RACE_CONTROL_PING}>", embed=embed)
    await interaction.response.send_message("Pomyślnie wysłano powiadomienie Race Control!", ephemeral=True)

@tree.command(name="rejestracja", description="rejestracja")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(wynik="True/False", uzytkownik="użytkownik", opis="opis decyzji")
async def rejestracja_command(interaction: discord.Interaction, wynik: str, uzytkownik: discord.Member, opis: str):
    await interaction.response.send_message("Wykonano", ephemeral=True)

    if wynik.lower() == "true": # Użyj .lower() dla elastyczności
        embed = discord.Embed(
            title=f"Wynik rejestracji - {uzytkownik.name}",
            description=f"**Twoja rejestracja została rozpatrzona pozytywnie!**\n**Notatka:** {opis}",
            color=hex_color("#00FF00")
        )
        embed.set_footer(text="Official Polish Racing Fortnite")
        await interaction.channel.send(content=uzytkownik.mention, embed=embed)
        
        # Pamiętaj, aby role istniały na serwerze!
        role_1 = interaction.guild.get_role(1187472243429740627)
        role_2 = interaction.guild.get_role(1359178553253695681)
        
        if role_1:
            await uzytkownik.add_roles(role_1)
        if role_2:
            await uzytkownik.add_roles(role_2)
        
    else:
        embed = discord.Embed(
            title=f"Wynik rejestracji - {uzytkownik.name}",
            description=f"**Twoja rejestracja została rozpatrzona negatywnie!**\n**Notatka:** {opis}",
            color=hex_color("#ff0000")
        )
        embed.set_footer(text="Official Polish Racing Fortnite")
        await interaction.channel.send(content=uzytkownik.mention, embed=embed)

@tree.command(name="twitter", description="Opublikuj Posta na Twitterze")
@app_commands.describe(obraz="Obraz (opcjonalny)")
async def twitter_command(interaction: discord.Interaction, obraz: Optional[discord.Attachment] = None):
    await interaction.response.send_modal(TwitterModal(image=obraz))

@tree.command(name="news", description="Opublikuj Newsa!")
@app_commands.describe(obraz="Obraz (opcjonalny)")
async def news_command(interaction: discord.Interaction, obraz: Optional[discord.Attachment] = None):
    # ID Roli, którą chcesz wzmiankować nad embedem newsa
    ROLE_ID_FOR_NEWS_MENTION = 1274060061911814288 # <<-- ZMIEŃ TO NA PRAWDZIWE ID ROLI, NP. ROLA "NEWSY" LUB "OGŁOSZENIA"

    # Lista emotek, którymi bot ma zareagować na newsa
    REACTIONS_FOR_NEWS = ["🔁"] # Możesz dodać więcej emotek

    # Sprawdzanie uprawnień administratora dla komendy news
    # NEWS_ROLE_ID służy do sprawdzania, czy użytkownik ma uprawnienia do użycia komendy news
    # ROLE_ID_FOR_NEWS_MENTION służy do wzmianki roli w wysyłanej wiadomości
    ADMIN_NEWS_ROLE_ID = 1187471587931336811 # To jest to samo ID, które miałeś wcześniej, służy do autoryzacji
    
    # Lepiej sprawdzić, czy użytkownik ma uprawnienia administratora na serwerze
    # lub określoną rolę, która pozwala mu wysyłać newsy.
    # W twoim kodzie używasz `NEWS_ROLE_ID` do sprawdzenia.
    # Zostawię to tak, jak miałeś, ale zmieniam nazwę zmiennej na bardziej czytelną.
    
    if not interaction.user.guild_permissions.administrator and not discord.utils.get(interaction.user.roles, id=ADMIN_NEWS_ROLE_ID):
        await interaction.response.send_message("Nie posiadasz odpowiednich uprawnień do publikowania newsów!", ephemeral=True)
        return

    # Przekazujemy ID roli i listę reakcji do NewsModal
    await interaction.response.send_modal(NewsModal(image=obraz, role_id=ROLE_ID_FOR_NEWS_MENTION, bot_reactions=REACTIONS_FOR_NEWS))

# --- BŁĘDY ---
@bot.event
async def on_command_error(ctx, error):
    error_message = ""

    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        error_message = "❌ Nie masz wystarczających uprawnień, aby użyć tej komendy."
    elif isinstance(error, commands.MissingRequiredArgument):
        error_message = f"❌ Brakuje wymaganego argumentu: `{error.param.name}`. Sprawdź użycie komendy!"
    elif isinstance(error, commands.BadArgument):
        error_message = "❌ Podałeś nieprawidłowy argument. Sprawdź, czy wpisałeś go poprawnie!"
    else:
        error_message = "❌ Wystąpił nieoczekiwany błąd podczas wykonywania komendy. Zgłoś to administratorowi!"
        print(f"Wystąpił nieznany błąd w komendzie '{ctx.command}' wywołanej przez {ctx.author}: {error}")

    if error_message:
        try:
            await ctx.reply(error_message, delete_after=10)
        except discord.HTTPException:
            pass

    if not isinstance(error, commands.CommandNotFound):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

# --- START BOTA ---
if __name__ == "__main__":
    TOKEN = "TWÓJ_TOKEN_TUTAJ" # Pamiętaj, aby tutaj wstawić swój token bota
    if not TOKEN or TOKEN == "TWÓJ_TOKEN_TUTAJ":
        print("❌ Ustaw swój token bota w kodzie!")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Nieprawidłowy token!")
        except Exception as e:
            print(f"❌ Błąd: {e}")
