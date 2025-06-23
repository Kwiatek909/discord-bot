import discord
from discord.ext import commands
import os

# Tworzenie bota
bot = commands.Bot(command_prefix=';', intents=discord.Intents.all())

# Event: bot gotowy
@bot.event
async def on_ready():
    print(f'Bot {bot.user} jest gotowy!')

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.CustomActivity(name="Przerwa Techniczna ⚠️")
    )

# Komenda ping z cooldownem
@bot.command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def ping(ctx):
    ping_ms = round(bot.latency * 1000)
    await ctx.send(f'🏓 Ping poprawny {ping_ms}ms')

# Obsługa błędów
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'⏳ Komenda jest na cooldownie. Spróbuj za {round(error.retry_after, 1)} sekundy.')
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send('❌ Nie istnieje taka komenda.')
    else:
        # Inne błędy — pokaż w konsoli (do debugowania)
        raise error

# Komenda zmiany statusu
@bot.command()
async def status(ctx, *, new_status):
    """Zmienia status bota"""
    await bot.change_presence(activity=discord.CustomActivity(name=new_status))
    await ctx.send(f'✅ Status zmieniony na: {new_status}')

# Uruchomienie bota
bot.run(os.getenv('DISCORD_TOKEN'))
