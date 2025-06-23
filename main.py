import discord
from discord.ext import commands
import os
import sys
import atexit
import asyncio

# Konfiguracja bota
bot = commands.Bot(
    command_prefix=';',
    intents=discord.Intents.all(),
    help_command=None
)

# --- ID kanałów (zmień te wartości!) ---
CHANNEL_ID_PING = "1246818926604582984"  # Kanał do wysyłania pingów co 10 minut
# CHANNEL_ID_LOGS = "123..."  # Przykład: możesz dodać inne kanały dla różnych funkcji

# --- Zabezpieczenie przed podwójnym uruchomieniem ---
LOCK_FILE = "/tmp/discord_bot.lock"

def cleanup():
    """Usuń plik blokady przy wyjściu"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

if os.path.exists(LOCK_FILE):
    print("Bot jest już uruchomiony! Zamykanie duplikatu...")
    sys.exit(0)
else:
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(cleanup)

# --- Funkcja do wysyłania pingów co 10 minut ---
async def send_ping():
    await bot.wait_until_ready()
    channel = bot.get_channel(int(CHANNEL_ID_PING))  # Używa CHANNEL_ID_PING
    if channel:
        while not bot.is_closed():
            try:
                await channel.send("Ping! (utrzymanie aktywności)")
                print(f"Wysłano ping na kanał {CHANNEL_ID_PING}!")
            except Exception as e:
                print(f"Błąd przy wysyłaniu pinga: {e}")
            await asyncio.sleep(600)  # 10 minut = 600 sekund

# --- Eventy ---
@bot.event
async def on_ready():
    print(f"Bot {bot.user} działa (PID: {os.getpid()})")
    await bot.change_presence(
        activity=discord.CustomActivity(name="Gotowy do działania"),
        status=discord.Status.online
    )
    # Uruchomienie tła (ping co 10 minut)
    bot.loop.create_task(send_ping())

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Poczekaj {round(error.retry_after, 1)} sekund przed ponownym użyciem.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Nieznana komenda. Wpisz ';pomoc'")
    else:
        print(f"Błąd: {error}")
        await ctx.send("Wystąpił błąd.")

# --- Komendy ---
@bot.command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def ping(ctx):
    """Sprawdź ping bota"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Ping: {latency}ms")

@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx, *, text: str):
    """Zmień status bota (tylko admin)"""
    await bot.change_presence(activity=discord.CustomActivity(name=text))
    await ctx.send(f"Status zmieniony na: {text}")

@bot.command()
async def pomoc(ctx):
    """Pokazuje listę komend"""
    embed = discord.Embed(
        title="Dostępne komendy",
        description=f"Prefix: {bot.command_prefix}",
        color=0xFFFFFF  # Biały kolor
    )
    embed.add_field(name="ping", value="Sprawdź opóźnienie bota", inline=False)
    embed.add_field(name="status [tekst]", value="Zmień status (tylko admin)", inline=False)
    await ctx.send(embed=embed)

# --- Uruchomienie ---
try:
    bot.run(os.getenv('DISCORD_TOKEN'))
except Exception as e:
    print(f"Krytyczny błąd: {e}")
    cleanup()
    sys.exit(1)
