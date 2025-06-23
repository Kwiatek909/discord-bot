import discord
from discord.ext import commands
import os

bot = commands.Bot(command_prefix=';', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Bot {bot.user} jest gotowy!')
    
    # Ustawianie statusu z samym tekstem (bez "Gra w")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.CustomActivity(name="Przerwa Techniczna ⚠️")
    )

@command_name.error
    async def command_name_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            em = discord.Embed(title=f"Odczekaj chwilę!",description=f"Spróbuj ponownie za {error.retry_after:.2f}s.", color=color_code_here)
            await ctx.send(embed=em)

@bot.command()
@commands.cooldown(1,15,commands.BucketType.user)
async def ping(ctx):
    ping_ms = round(bot.latency * 1000)
    await ctx.send(f'Ping poprawny {ping_ms}ms')

# Komenda do zmiany statusu (opcjonalna)
@bot.command()
async def status(ctx, *, new_status):
    """Zmienia status bota"""
    await bot.change_presence(activity=discord.CustomActivity(name=new_status))
    await ctx.send(f'Status zmieniony na: {new_status}')

bot.run(os.getenv('DISCORD_TOKEN'))
