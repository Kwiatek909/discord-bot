import discord
from discord.ext import commands
import os

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Bot {bot.user} jest gotowy!')
    
    # Ustawianie statusu bota
    await bot.change_presence(
        status=discord.Status.online,  # online, idle, dnd, invisible
        activity=discord.Game(name="Pomocny Bot")  # Co bot "gra"
    )

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# Komenda do zmiany statusu (opcjonalna)
@bot.command()
async def status(ctx, *, new_status):
    """Zmienia status bota"""
    await bot.change_presence(activity=discord.Game(name=new_status))
    await ctx.send(f'Status zmieniony na: {new_status}')

bot.run(os.getenv('DISCORD_TOKEN'))
