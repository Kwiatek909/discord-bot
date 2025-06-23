import discord
from discord.ext import commands
import os
import sys
import atexit

# Konfiguracja bota
bot = commands.Bot(
    command_prefix=';',
    intents=discord.Intents.all(),
    help_command=None  # Wyłącz domyślną komendę pomocy
)

# --- Zabezpieczenie przed podwójnym uruchomieniem ---
LOCK_FILE = "/tmp/discord_bot.lock"  # Ścieżka dla Render.com

def cleanup():
    """Usuń plik blokady przy wyjściu"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

if os.path.exists(LOCK_FILE):
    print("🛑 Bot jest już uruchomiony! Zamykanie duplikatu...")
    sys.exit(0)
else:
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))  # Zapisz PID procesu
    atexit.register(cleanup)  # Sprzątanie przy wyjściu

# --- Eventy ---
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} działa (PID: {os.getpid()})")
    await bot.change_presence(
        activity=discord.CustomActivity(name="Gotowy do działania!"),
        status=discord.Status.online
    )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Poczekaj {round(error.retry_after, 1)}s przed ponownym użyciem!")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Nieznana komenda! Wpisz `;pomoc`")
    else:
        print(f"❗ Błąd: {error}")
        await ctx.send("⚠️ Wystąpił błąd!")

# --- Komendy ---
@bot.command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def ping(ctx):
    """Sprawdź ping bota"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")

@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx, *, text: str):
    """Zmień status bota (tylko admin)"""
    await bot.change_presence(activity=discord.CustomActivity(name=text))
    await ctx.send(f"✅ Status ustawiony na: `{text}`")

@bot.command()
async def pomoc(ctx):
    """Pokazuje tę wiadomość"""
    embed = discord.Embed(
        title="📜 Dostępne komendy",
        description=f"Prefix: `{bot.command_prefix}`",
        color=0x00ff00
    )
    embed.add_field(name="🏓 ping", value="Sprawdź opóźnienie bota", inline=False)
    embed.add_field(name="🔧 status [tekst]", value="Zmień status (admin)", inline=False)
    await ctx.send(embed=embed)

# --- Uruchomienie ---
try:
    bot.run(os.getenv('DISCORD_TOKEN'))
except Exception as e:
    print(f"🚨 Krytyczny błąd: {e}")
    cleanup()  # Usuń plik blokady przy crashu
    sys.exit(1)
