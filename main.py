import discord
from discord.ext import commands
import os
import sys
import atexit
from flask import Flask
import logging
import threading

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegulaminModal(discord.ui.Modal, title='Propozycja zmiany regulaminu'):

    def __init__(self):
        super().__init__(timeout=300)
        self.temat = discord.ui.TextInput(
            label='Temat zmiany',
            placeholder='np. Punkt za Pole Position',
            required=True,
            max_length=100)
        self.powod = discord.ui.TextInput(
            label='Powód zmiany',
            placeholder='np. Dodatkowy punkt dla czołówki',
            required=True,
            max_length=200)
        self.uzasadnienie = discord.ui.TextInput(
            label='Szczegółowe uzasadnienie',
            style=discord.TextStyle.paragraph,
            placeholder=
            'Wyjaśnij dlaczego ta zmiana powinna zostać wprowadzona...',
            required=True,
            max_length=1000)

        self.add_item(self.temat)
        self.add_item(self.powod)
        self.add_item(self.uzasadnienie)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="Zmiana Regulacji",  # Stały tytuł
                color=0xFF8C00,
                timestamp=discord.utils.utcnow())

            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.avatar.url if interaction.user.avatar
                else interaction.user.default_avatar.url)

            # Prostsze formatowanie bez tagów i automatycznych podpisów
            embed.add_field(name="Co należy zmienić?",
                            value=self.temat.value,
                            inline=False)
            embed.add_field(name="Powód zmiany",
                            value=self.powod.value,
                            inline=False)
            embed.add_field(name="Uzasadnienie",
                            value=self.uzasadnienie.value,
                            inline=False)

            embed.set_thumbnail(
                url=
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/1200px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png"
            )
            embed.set_footer(text="Czekaj na wynik twojego formularza"
                             )  # Taka sama stopka jak w innych

            await interaction.response.send_message(
                "✅ Twoja propozycja zmiany regulaminu została wysłana!",
                ephemeral=True)
            await interaction.channel.send(embed=embed)

        except Exception as e:
            await self.on_error(interaction, e)

    async def on_error(self, interaction: discord.Interaction,
                       error: Exception):
        await interaction.response.send_message(
            "❌ Wystąpił błąd podczas wysyłania formularza.", ephemeral=True)
        logger.error(f"Błąd w formularzu regulaminu: {error}")


class ZglosModal(discord.ui.Modal, title='Zgłoś skład'):

    def __init__(self):
        super().__init__(timeout=300)
        self.zglos_sklad = discord.ui.TextInput(
            label='Zespół',
            placeholder='Oracle Red Bull Racing RBPT',
            required=True,
            max_length=100)
        self.kierowcy = discord.ui.TextInput(
            label='Kierowcy',
            placeholder='Person #99, Orzelke #53',
            required=True,
            max_length=200)
        self.akademia = discord.ui.TextInput(label='Akademia',
                                             placeholder='RedBull',
                                             required=True,
                                             max_length=100)
        self.grand_prix_dywizja = discord.ui.TextInput(
            label='Grand Prix i Dywizja',
            placeholder='R3 - GP Japonia - S6, F1',
            required=True,
            max_length=150)

        self.add_item(self.zglos_sklad)
        self.add_item(self.kierowcy)
        self.add_item(self.akademia)
        self.add_item(self.grand_prix_dywizja)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title="Zgłoszenie składu",
                                  color=0xFF8C00,
                                  timestamp=discord.utils.utcnow())

            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.avatar.url if interaction.user.avatar
                else interaction.user.default_avatar.url)

            embed.add_field(name="Zespół",
                            value=self.zglos_sklad.value,
                            inline=False)
            embed.add_field(name="Kierowcy",
                            value=self.kierowcy.value,
                            inline=False)
            embed.add_field(name="Akademia",
                            value=self.akademia.value,
                            inline=False)

            gp_dywizja = self.grand_prix_dywizja.value.split(',')
            embed.add_field(name="Grand Prix",
                            value=gp_dywizja[0].strip(),
                            inline=False)
            embed.add_field(
                name="Dywizja",
                value=gp_dywizja[1].strip() if len(gp_dywizja) > 1 else "N/A",
                inline=False)

            embed.set_thumbnail(
                url=
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/1200px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png"
            )
            embed.set_footer(text="Czekaj na wynik twojego zgłoszenia")

            await interaction.response.send_message(
                "✅ Twoje zgłoszenie zostało wysłane!", ephemeral=True)
            channel = interaction.guild.get_channel(
                123456789)  # ZASTĄP PRAWDZIWYM ID KANAŁU
            if channel:
                await channel.send(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await self.on_error(interaction, e)

    async def on_error(self, interaction: discord.Interaction,
                       error: Exception):
        await interaction.response.send_message(
            "❌ Wystąpił błąd podczas wysyłania formularza.", ephemeral=True)
        logger.error(f"Błąd w modalnym formularzu zgłoszenia: {error}")


class OdwolanieModal(discord.ui.Modal, title='Odwołanie od kary'):

    def __init__(self):
        super().__init__(timeout=300)
        self.dane_kierowcy = discord.ui.TextInput(label='Dane Kierowcy',
                                                  placeholder='Maklini #95',
                                                  required=True,
                                                  max_length=100)
        self.grand_prix = discord.ui.TextInput(label='Grand Prix',
                                               placeholder='S3-R8-GP Holandii',
                                               required=True,
                                               max_length=100)
        self.zamieszani = discord.ui.TextInput(
            label='Zamieszani',
            placeholder='Kamil #32, Mesterek #27, Stravbo #12',
            required=True,
            max_length=200)
        self.tresc = discord.ui.TextInput(
            label='Treść',
            placeholder='Szanowne FIA, Witam was serdecznie...',
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000)

        self.add_item(self.dane_kierowcy)
        self.add_item(self.grand_prix)
        self.add_item(self.zamieszani)
        self.add_item(self.tresc)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title="Odwołanie od kary",
                                  color=0xFF8C00,
                                  timestamp=discord.utils.utcnow())

            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.avatar.url if interaction.user.avatar
                else interaction.user.default_avatar.url)

            embed.add_field(name="Dane Kierowcy",
                            value=self.dane_kierowcy.value,
                            inline=False)
            embed.add_field(name="Grand Prix",
                            value=self.grand_prix.value,
                            inline=False)
            embed.add_field(name="Zamieszani",
                            value=self.zamieszani.value,
                            inline=False)
            embed.add_field(name="Treść", value=self.tresc.value, inline=False)

            embed.set_thumbnail(
                url=
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/1200px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png"
            )
            embed.set_footer(text="Czekaj na wynik twojego formularza")

            await interaction.response.send_message(
                "✅ Twoje odwołanie zostało wysłane!", ephemeral=True)
            channel = interaction.guild.get_channel(
                123456789)  # ZASTĄP PRAWDZIWYM ID KANAŁU
            if channel:
                await channel.send(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await self.on_error(interaction, e)

    async def on_error(self, interaction: discord.Interaction,
                       error: Exception):
        await interaction.response.send_message(
            "❌ Wystąpił błąd podczas wysyłania formularza.", ephemeral=True)
        logger.error(f"Błąd w modalnym formularzu odwołania: {error}")


# Serwer Flask dla UptimeRobot
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot działa 24/7!"


def keep_alive():

    def run_flask():
        try:
            app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"Błąd Flaska: {e}")

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()


# Konfiguracja bota
bot = commands.Bot(command_prefix=';',
                   intents=discord.Intents.all(),
                   help_command=None)

# --- Zabezpieczenie przed podwójnym uruchomieniem ---
LOCK_FILE = "/tmp/discord_bot.lock"


def cleanup():
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
            logger.info("Plik blokady usunięty")
        except Exception as e:
            logger.error(f"Błąd podczas usuwania pliku blokady: {e}")


if os.path.exists(LOCK_FILE):
    try:
        with open(LOCK_FILE, "r") as f:
            old_pid = int(f.read().strip())
        if os.path.exists(
                f"/proc/{old_pid}"):  # Sprawdź czy proces istnieje (Linux)
            print(
                f"Bot jest już uruchomiony! (PID: {old_pid}) Zamykanie duplikatu..."
            )
            sys.exit(0)
        else:
            os.remove(LOCK_FILE)
    except Exception as e:
        print(f"Błąd przy sprawdzaniu pliku blokady: {e}")
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))
atexit.register(cleanup)


# --- Eventy i komendy ---
@bot.event
async def on_ready():
    logger.info(f"Bot {bot.user} działa!")
    await bot.change_presence(
        activity=discord.CustomActivity(name="Przerwa Techniczna ⚠️"),
        status=discord.Status.online)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"Poczekaj {round(error.retry_after, 1)} sekund przed ponownym użyciem."
        )
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Nieznana komenda. Wpisz ;pomoc")
    else:
        logger.error(f"Błąd: {error}")
        await ctx.send("Wystąpił błąd.")


@bot.command()
async def twitter(ctx):
    """Sends a Twitter post embed with optional attachment."""
    await ctx.send("Click to fill out the form.")
    await ctx.send_modal(TwitterModal())


class TwitterModal(discord.ui.Modal, title='Nowy Post Twitter'):
    title = discord.ui.TextInput(label='Tytuł', max_length=100, required=True)
    content = discord.ui.TextInput(label='Treść',
                                   style=discord.TextStyle.paragraph,
                                   required=True)
    attachment = discord.ui.TextInput(label='URL Zdjęcia (opcjonalne)',
                                      required=False)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.title.value,
            description=self.content.value,
            color=0x1DA1F2  # Light blue color, Twitter's brand color
        )

        if self.attachment.value:
            embed.set_image(url=self.attachment.value)
        # Replace CHANNEL_ID with the actual ID of the channel where you want to send the embed
        channel = interaction.guild.get_channel(
            1282096776928559246)  # ZASTĄP PRAWDZIWYM ID KANAŁU
        if channel:
            await channel.send(embed=embed)
            await interaction.response.send_message(
                "✅ Post na Twitterze został wysłany!", ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Nie mogę znaleźć kanału!", ephemeral=True)


# Don't forget to add your command handling code after defining the command and modal.


@bot.command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def ping(ctx):
    """Sprawdź ping bota"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Ping: {latency}ms")


@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx, *, text: str):
    """Zmień status bota"""
    await bot.change_presence(activity=discord.CustomActivity(name=text))
    await ctx.send(f"Status zmieniony na: {text}")


@bot.command()
async def pomoc(ctx):
    """Pokazuje listę komend"""
    embed = discord.Embed(title="📜 Dostępne komendy",
                          description=f"Prefix: {bot.command_prefix}",
                          color=0xFFFFFF)
    embed.add_field(name="ping", value="Sprawdź opóźnienie bota", inline=False)
    embed.add_field(name="status [tekst]",
                    value="Zmień status (tylko admin)",
                    inline=False)
    embed.add_field(name="wnioski",
                    value="Wyślij formularz wniosków",
                    inline=False)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def wnioski(ctx):
    """Wyślij formularz wniosków do FIA"""
    embed = discord.Embed(
        title="Wnioski",
        description=("Napisz oficjalny wniosek do FIA.\n"
                     "Pamiętaj o wymogach podczas pisania.\n"
                     "Kliknąć przycisk wyświetli ci się okienko\n"
                     "w którym będziesz mógł stworzyć wniosek.\n"
                     "Stosuję się do przykładów.\n\n"),
        color=0xFF8C00)
    embed.set_footer(
        text="Wniosek może być odrzucony z powodu złej pisowni lub formatu.")
    embed.set_thumbnail(
        url=
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg/1200px-F%C3%A9d%C3%A9ration_Internationale_de_l%27Automobile_wordmark.svg.png"
    )

    view = discord.ui.View(timeout=None)

    odwolanie_button = discord.ui.Button(label="Odwołanie od kary",
                                         style=discord.ButtonStyle.success,
                                         emoji="📋")
    regulamin_button = discord.ui.Button(label="Regulamin",
                                         style=discord.ButtonStyle.success,
                                         emoji="📄")
    zgloszenie_button = discord.ui.Button(label="Zgłoś skład",
                                          style=discord.ButtonStyle.success,
                                          emoji="📋")

    async def odwolanie_callback(interaction):
        await interaction.response.send_modal(OdwolanieModal())

    async def regulamin_callback(interaction):
        await interaction.response.send_modal(RegulaminModal())

    async def zgloszenie_callback(interaction):
        await interaction.response.send_modal(ZglosModal())

    odwolanie_button.callback = odwolanie_callback
    regulamin_button.callback = regulamin_callback
    zgloszenie_button.callback = zgloszenie_callback

    view.add_item(odwolanie_button)
    view.add_item(regulamin_button)
    view.add_item(zgloszenie_button)

    try:
        await ctx.message.delete()
    except:
        pass

    await ctx.send(embed=embed, view=view)


# --- Uruchomienie ---
if __name__ == '__main__':
    logger.info("Uruchamianie bota...")
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.critical(
            "BRAK TOKENU! Ustaw zmienną środowiskową DISCORD_TOKEN")
        sys.exit(1)

    keep_alive()
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.critical("Nieprawidłowy token Discord!")
    except Exception as e:
        logger.critical(f"Krytyczny błąd: {e}")
        cleanup()
        sys.exit(1)
        
