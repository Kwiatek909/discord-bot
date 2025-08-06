import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional
from datetime import datetime, timezone
import random
import json
import os
import time
import re

# --- Funkcje pomocnicze ---
def hex_color(hex_str):
    return discord.Color(int(hex_str.lstrip('#'), 16))

# --- Konfiguracja bota ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Potrzebne do pobierania ról użytkownika

bot = commands.Bot(command_prefix=';', intents=intents, help_command=None)
tree = bot.tree

# --- Nazwy plików bazy danych ---
DB_FILE = 'data.json'
DRIVERS_FILE = 'drivers.json'

# --- Globalne zmienne do przechowywania danych i ich czasów modyfikacji ---
bot_data = {}
last_data_reload_time = 0.0 # Czas ostatniej modyfikacji DB_FILE

all_drivers_data = [] # WAŻNE: Zostanie załadowana w on_ready
last_drivers_load_time = 0.0 # NOWA ZMIENNA: Czas ostatniej modyfikacji DRIVERS_FILE

# --- Funkcje ładowania/zapisywania danych ---
def load_data():
    """Ładuje dane użytkowników z pliku JSON."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ostrzeżenie: Plik {DB_FILE} jest uszkodzony lub pusty. Zwracam pusty słownik.")
            return {}
    return {}

def save_data(data):
    """Zapisuje dane użytkowników do pliku JSON."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_drivers_data():
    """Ładuje dane o kierowcach z pliku JSON."""
    if os.path.exists(DRIVERS_FILE):
        try:
            with open(DRIVERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ostrzeżenie: Plik {DRIVERS_FILE} jest uszkodzony lub pusty. Zwracam pustą listę.")
            return []
    return [] # Zwróć pustą listę, jeśli plik nie istnieje

# --- Funkcje pomocnicze do pobierania danych użytkownika ---
def get_user_coins(user_id):
    """Pobiera liczbę oprf_coins użytkownika."""
    user_id_str = str(user_id)
    # Zawsze przeładowuj dane, aby być pewnym aktualności
    global bot_data, last_data_reload_time
    if os.path.exists(DB_FILE):
        current_file_mtime = os.path.getmtime(DB_FILE)
        if current_file_mtime > last_data_reload_time:
            bot_data = load_data()
            last_data_reload_time = current_file_mtime
    return bot_data.get(user_id_str, {}).get("oprf_coins", 0)

def get_user_paczki(user_id):
    """Pobiera liczbę paczek użytkownika."""
    user_id_str = str(user_id)
    # Zawsze przeładowuj dane, aby być pewnym aktualności
    global bot_data, last_data_reload_time
    if os.path.exists(DB_FILE):
        current_file_mtime = os.path.getmtime(DB_FILE)
        if current_file_mtime > last_data_reload_time:
            bot_data = load_data()
            last_data_reload_time = current_file_mtime
    return bot_data.get(user_id_str, {}).get("paczki", 0)

def get_user_cards(user_id):
    """Pobiera listę kart kierowców użytkownika."""
    user_id_str = str(user_id)
    # Zawsze przeładowuj dane, aby być pewnym aktualności
    global bot_data, last_data_reload_time
    if os.path.exists(DB_FILE):
        current_file_mtime = os.path.getmtime(DB_FILE)
        if current_file_mtime > last_data_reload_time:
            bot_data = load_data()
            last_data_reload_time = current_file_mtime
    return bot_data.get(user_id_str, {}).get("karty", [])

# --- Eventy bota ---
@bot.event
async def on_ready():
    global bot_data, last_data_reload_time, all_drivers_data, last_drivers_load_time

    # KROK 1: Wczytaj dane użytkowników (data.json)
    if os.path.exists(DB_FILE):
        try:
            bot_data = load_data()
            last_data_reload_time = os.path.getmtime(DB_FILE)
            print(f"Pomyślnie załadowano dane użytkowników z {DB_FILE}.")
        except Exception as e:
            print(f"Błąd podczas ładowania {DB_FILE} w on_ready: {e}. Inicjalizuję puste dane.")
            bot_data = {}
            last_data_reload_time = 0.0
    else:
        print(f"Plik {DB_FILE} nie istnieje. Inicjalizuję puste dane użytkowników.")
        bot_data = {}
        save_data(bot_data) # Opcjonalnie: stwórz pusty plik od razu, by uniknąć błędów
        last_data_reload_time = 0.0

    # KROK 2: Wczytaj dane kierowców (drivers.json)
    if os.path.exists(DRIVERS_FILE):
        try:
            all_drivers_data = load_drivers_data()
            last_drivers_load_time = os.path.getmtime(DRIVERS_FILE)
            print(f"Pomyślnie załadowano {len(all_drivers_data)} kierowców z {DRIVERS_FILE}.")
        except Exception as e:
            print(f"Błąd podczas ładowania {DRIVERS_FILE} w on_ready: {e}. Lista kierowców będzie pusta.")
            all_drivers_data = []
            last_drivers_load_time = 0.0
    else:
        print(f"BŁĄD: Plik {DRIVERS_FILE} nie istnieje! Funkcje związane z kartami kierowców mogą nie działać.")
        all_drivers_data = []
        last_drivers_load_time = 0.0

    # KROK 3: Synchronizacja komend i ustawienie statusu bota
    await tree.sync()
    print(f'{bot.user} jest online!')
    activity = discord.Activity(type=discord.ActivityType.listening, name="/pomoc")
    await bot.change_presence(activity=activity)
    
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    SPECJALNY_UZYTKOWNIK_ID = 784336822104227841

    if message.author.id == SPECJALNY_UZYTKOWNIK_ID:
        tresc = message.content.lower()
        slowa_w_wiadomosci = set(re.findall(r'\w+', tresc))
        wymagane_slowa = {"psem", "spacer", "pies"}

        # Sprawdza, czy przynajmniej jedno słowo z wymagane_slowa jest w slowa_w_wiadomosci
        if wymagane_slowa.intersection(slowa_w_wiadomosci):
            await message.reply("https://cdn.discordapp.com/attachments/1187471588535320596/1397663795655999549/kubon.gif")

    await bot.process_commands(message)
    
# --- Przykładowe komendy (MUSISZ DODAĆ SWOJE KOMENDY TUTAJ) ---
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

@bot.command(name='coinsy')
async def coinsy(ctx, value: int):
    """
    Komenda dla administratorów do wysyłania coinsów do zebrania przez użytkowników.
    """
    # Sprawdzenie czy użytkownik ma uprawnienia administratora
    if not ctx.author.guild_permissions.administrator:
        print(f"Użytkownik {ctx.author} (ID: {ctx.author.id}) próbował użyć komendy '{ctx.command.name}', ale nie posiada uprawnień administratora.")
        return

    # Sprawdzenie czy wartość jest dodatnia
    if value <= 0:
        await ctx.send("Wartość musi być większa od 0!", delete_after=5)
        return

    # Usunięcie oryginalnej wiadomości z komendą
    await ctx.message.delete()

    # Tworzenie przycisku do zebrania coinsów
    collect_button = discord.ui.Button(
        label="Zbierz",
        style=discord.ButtonStyle.success,
        emoji="🪙",
        custom_id=f"collect_coins_{value}"
    )

    view = discord.ui.View(timeout=None)  # Bez timeout, żeby przycisk działał długo
    view.add_item(collect_button)

    # Lista użytkowników którzy już zebrali coinsy (żeby nie mogli zebrać drugi raz)
    collected_users = set()

    async def collect_button_callback(interaction: discord.Interaction):
        user_id = interaction.user.id
        user_mention = interaction.user.mention

        # Sprawdzenie czy użytkownik już zebrał coinsy
        if user_id in collected_users:
            await interaction.response.send_message(
                "Już zebrałeś te coinsy!", 
                ephemeral=True
            )
            return

        # Dodanie użytkownika do listy tych którzy zebrali
        collected_users.add(user_id)

        # Przeładowanie danych użytkownika
        user_id_str = str(user_id)
        global bot_data, last_data_reload_time
        if os.path.exists(DB_FILE):
            current_file_mtime = os.path.getmtime(DB_FILE)
            if current_file_mtime > last_data_reload_time:
                bot_data = load_data()
                last_data_reload_time = current_file_mtime

        # Inicjalizacja danych dla nowego użytkownika
        if user_id_str not in bot_data:
            bot_data[user_id_str] = {
                "user_name": interaction.user.name,
                "oprf_coins": 0,
                "paczki": 0,
                "karty": []
            }

        # Dodanie coinsów
        bot_data[user_id_str]["oprf_coins"] += value
        
        # Zapisanie danych
        save_data(bot_data)

        # Utworzenie zaktualizowanego embeda
        updated_embed = discord.Embed(
            title="Monety zebrane!",
            description=f"{value} OPRF Coinsów zebrał {user_mention}",
            color=hex_color("#FFFFFF")
        )

        # Wysłanie efemerycznej wiadomości do użytkownika
        await interaction.response.send_message(
            f"**Gratulacje!** Pomyślnie zebrałeś `{value}` OPRF Coinsów!",
            ephemeral=True
        )
        
        # Wyłączenie przycisku
        collect_button.disabled = True
        
        # Aktualizacja oryginalnej wiadomości (tej z embedem "Zbierz X OPRF Coinsów")
        await interaction.message.edit(embed=updated_embed, view=view)

    collect_button.callback = collect_button_callback

    # Tworzenie początkowego embeda
    initial_embed = discord.Embed(
        title=f"Zbierz {value} OPRF Coinsów",
        color=hex_color("#FFFFFF")
    )

    # Wysłanie wiadomości
    await ctx.send(embed=initial_embed, view=view)
    
@tree.command(name="pitstop-game", description="Pobierz grę OPRF Pitstop Game")
async def pitstop_game(interaction: discord.Interaction):
    """
    Prosta komenda ukośnikowa, która odpowiada efemeryczną wiadomością.
    """
    user_mention = interaction.user.mention  # Pobiera oznaczenie użytkownika
    response_content = f"`Link`: https://kwiatek909.github.io/oprf-website/ \n{user_mention} życzymy Ci miłej zabawy!"
    await interaction.response.send_message(response_content, ephemeral=True)
    
# --- Zmodyfikowana komenda /sklep (używa nowej logiki ładowania) ---
@tree.command(name="sklep", description="Odwiedź sklep OPRF!")
@app_commands.guild_only()
async def sklep_command(interaction: discord.Interaction):
    thumbnail_url = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None

    buy_pack_button = discord.ui.Button(
        label="Kup paczkę Kierowcy OPRF",
        style=discord.ButtonStyle.success,
        emoji="📦",
        custom_id="zakuppaczka"
    )

    view = discord.ui.View(timeout=180)
    view.add_item(buy_pack_button)

    async def buy_pack_button_callback(interaction: discord.Interaction):
        user_id = interaction.user.id
        user_display_name = interaction.user.display_name

        # DANE UŻYTKOWNIKA SĄ JUŻ ZAKTUALIZOWANE W get_user_coins
        item_cost = 25
        current_coins = get_user_coins(user_id) # Ta funkcja już przeładowuje dane!

        if current_coins >= item_cost:
            user_id_str = str(user_id)
            if user_id_str not in bot_data: # Inicjalizacja dla nowych użytkowników
                bot_data[user_id_str] = {
                    "user_name": interaction.user.name,
                    "oprf_coins": 0,
                    "paczki": 0,
                    "karty": []
                }
            
            # Pobieramy paczki po przeładowaniu danych
            current_paczki = get_user_paczki(user_id) 
            
            bot_data[user_id_str]["oprf_coins"] -= item_cost
            bot_data[user_id_str]["paczki"] += 1
            
            save_data(bot_data) # Zapisujemy zmiany

            await interaction.response.send_message(
                f"**Gratulacje, {user_display_name}!** Pomyślnie zakupiono paczkę Kierowcy OPRF. "
                f"Masz teraz `{bot_data[user_id_str]['oprf_coins']}` OPRF Coinsów i `{bot_data[user_id_str]['paczki']}` paczek.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"**{user_display_name}**, masz tylko `{current_coins}` OPRF Coinsów. Potrzebujesz `{item_cost}` OPRF Coinsów, aby kupić paczkę.",
                ephemeral=True
            )

    buy_pack_button.callback = buy_pack_button_callback

    embed = discord.Embed(
        title="Sklep OPRF 🛒",
        description="Witaj w sklepie discord Official Polish Racing Fortnite!\n"
                    "**Przedmioty**\n"
                    "- Paczka Kierowcy OPRF `25 OPRF Coins`",
        color=hex_color("#FFFFFF")
    )
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Official Polish Racing Fortnite")

    await interaction.response.send_message(embed=embed, view=view)


# --- Zmodyfikowana komenda /konto (z oceną ogólną przy kartach) ---
@tree.command(name="konto", description="Wyświetla informacje o koncie!")
@app_commands.describe(member="Opcjonalnie: Użytkownik, którego konto chcesz sprawdzić.")
async def konto_command(interaction: discord.Interaction, member: discord.Member = None):
    # DANE UŻYTKOWNIKA SĄ JUŻ ZAKTUALIZOWANE W get_user_coins itp.
    target_user = member if member else interaction.user
    user_id = target_user.id

    # Inicjalizacja danych dla użytkownika, jeśli ich jeszcze nie ma lub brakuje pola 'karty'
    user_id_str = str(user_id)
    if user_id_str not in bot_data: # Używamy bot_data, które zostało zaktualizowane przez get_user_coins/paczki/cards
        bot_data[user_id_str] = {
            "user_name": target_user.name,
            "oprf_coins": 0,
            "paczki": 0,
            "karty": []
        }
        save_data(bot_data) # Zapisujemy nowego użytkownika
    elif "karty" not in bot_data[user_id_str]:
        bot_data[user_id_str]["karty"] = []
        save_data(bot_data)

    coins = get_user_coins(user_id) # Te funkcje już dbają o przeładowanie
    paczki = get_user_paczki(user_id)
    karty = get_user_cards(user_id)

    # Sprawdź i przeładuj dane kierowców (jeśli plik się zmienił)
    global all_drivers_data, last_drivers_load_time
    if os.path.exists(DRIVERS_FILE):
        current_drivers_mtime = os.path.getmtime(DRIVERS_FILE)
        if current_drivers_mtime > last_drivers_load_time:
            all_drivers_data = load_drivers_data()
            last_drivers_load_time = current_drivers_mtime

    # Tworzenie listy kart z oceną ogólną
    if karty:
        cards_with_rating = []
        for karta in karty:
            # Znajdź kierowcę w danych all_drivers_data
            driver_data = None
            for driver in all_drivers_data:
                if driver['kierowca'] == karta:
                    driver_data = driver
                    break
            
            # Jeśli znaleziono dane kierowcy, dodaj ocenę ogólną
            if driver_data and driver_data.get('ocena_ogolna') is not None:
                cards_with_rating.append(f"{karta} ({driver_data['ocena_ogolna']})")
            else:
                # Jeśli nie znaleziono danych lub brak oceny, wyświetl tylko nazwę
                cards_with_rating.append(f"{karta} (Brak oceny)")
        
        cards_display = ", ".join(cards_with_rating)
    else:
        cards_display = "Brak kart"

    description_text = (
        f"**Stan Konta**\n"
        f"- Stan Konta: `{coins}` OPRF Coinsów\n"
        f"**Przedmioty**\n"
        f"- Paczki: `{paczki}`\n"
        f"- Karty: {cards_display}"
    )

    embed_title = f"Konto Użytkownika: {target_user.name}"

    embed = discord.Embed(
        title=embed_title,
        description=description_text,
        color=hex_color("#FFFFFF")
    )

    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
    embed.set_footer(text="Official Polish Racing Fortnite")

    await interaction.response.send_message(embed=embed, ephemeral=False)

# --- Zmodyfikowana komenda /paczka (używa nowej logiki ładowania) ---
@tree.command(name="paczka", description="Wyświetla paczkę do otwarcia.")
@app_commands.guild_only()
async def paczka_command(interaction: discord.Interaction):
    user_id = interaction.user.id
    current_paczki = get_user_paczki(user_id) # Ta funkcja już przeładowuje dane!

    if current_paczki < 1:
        await interaction.response.send_message(
            "Nie masz żadnych paczek do otwarcia! Kup je w `/sklep`.",
            ephemeral=True
        )
        return

    open_pack_button = discord.ui.Button(
        label="Otwórz Paczkę",
        style=discord.ButtonStyle.success,
        emoji="📦",
        custom_id="paczkaopen"
    )

    view = discord.ui.View(timeout=180)
    view.add_item(open_pack_button)

    async def open_pack_button_callback(interaction: discord.Interaction):
        user_id = interaction.user.id
        user_display_name = interaction.user.display_name

        # DANE UŻYTKOWNIKA SĄ JUŻ ZAKTUALIZOWANE PRZEZ get_user_paczki
        current_paczki_after_check = get_user_paczki(user_id) # Ponowne sprawdzenie po kliknięciu

        if current_paczki_after_check < 1:
            await interaction.response.send_message(
                "Wygląda na to, że nie masz już paczek! Być może właśnie ją otworzyłeś.",
                ephemeral=True
            )
            return

        user_id_str = str(user_id)
        # Te sprawdzenia są redundantne, jeśli get_user_paczki/cards zawsze inicjalizuje,
        # ale nie zaszkodzą, jeśli coś by się zmieniało w przyszłości.
        if user_id_str not in bot_data:
            bot_data[user_id_str] = {
                "user_name": interaction.user.name,
                "oprf_coins": 0,
                "paczki": 0,
                "karty": []
            }
        elif "karty" not in bot_data[user_id_str]:
            bot_data[user_id_str]["karty"] = []

        bot_data[user_id_str]["paczki"] -= 1

        # KROK: Sprawdź i przeładuj dane kierowców (jeśli plik się zmienił)
        global all_drivers_data, last_drivers_load_time # Dodaj last_drivers_load_time tutaj
        if os.path.exists(DRIVERS_FILE):
            current_drivers_mtime = os.path.getmtime(DRIVERS_FILE)
            if current_drivers_mtime > last_drivers_load_time: # Użyj last_drivers_load_time
                print(f"Wykryto zmiany w {DRIVERS_FILE}. Przeładowuję dane kierowców przed losowaniem...")
                all_drivers_data = load_drivers_data()
                last_drivers_load_time = current_drivers_mtime
        else:
            print(f"Plik {DRIVERS_FILE} nie istnieje. Nie ma kierowców do wylosowania.")
            await interaction.response.send_message(
                "Wystąpił błąd: brak danych o kierowcach. Skontaktuj się z administratorem.",
                ephemeral=True
            )
            return

        if not all_drivers_data:
            await interaction.response.send_message(
                "Brak dostępnych kart kierowców do wylosowania. Skontaktuj się z administratorem.",
                ephemeral=True
            )
            return

        chosen_driver = random.choice(all_drivers_data)
        bot_data[user_id_str]["karty"].append(chosen_driver['kierowca'])

        save_data(bot_data)

        reward_embed = discord.Embed(
            title=f"Karta Kierowcy - {chosen_driver['kierowca']}",
            description=(
                f"**Informacje Kierowcy:**\n"
                f"`Numer` - #{chosen_driver['numer']}\n"
                f"`Drużyna` - {chosen_driver['druzyna']}\n"
                f"`Ocena Ogólna` - {chosen_driver['ocena_ogolna'] if chosen_driver['ocena_ogolna'] is not None else 'Brak oceny'}"
            ),
            color=hex_color("#FFFFFF")
        )

        if 'link_thumbnail' in chosen_driver and chosen_driver['link_thumbnail']:
            reward_embed.set_thumbnail(url=chosen_driver['link_thumbnail'])
        if 'link' in chosen_driver and chosen_driver['link']:
            reward_embed.set_image(url=chosen_driver['link'])

        reward_embed.set_author(
            name=f"Otwarte przez - {user_display_name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        reward_embed.set_footer(text="Official Polish Racing Fortnite")

        await interaction.response.send_message(
            content=f"**{user_display_name}** otworzył paczkę i wylosował:",
            embed=reward_embed,
            ephemeral=False
        )

    open_pack_button.callback = open_pack_button_callback

    initial_embed = discord.Embed(
        title="Paczka 📦",
        description="Twoja paczka stoi przed tobą \ni czeka aż ją otworzysz!",
        color=hex_color("#FFFFFF")
    )
    initial_embed.set_image(url="https://cdn.discordapp.com/attachments/1268199863636594788/1399530452141998100/golden_pack_2.png?ex=688955cd&is=6888044d&hm=eb807ba604a5fd8979b66077744205abe240b32674b8038bb3a9eba984723f05&")
    initial_embed.set_footer(text="Official Polish Racing Fortnite")

    await interaction.response.send_message(embed=initial_embed, view=view, ephemeral=False)

@tree.command(name="lista-paczka", description="Wyświetla listę dostępnych kart w paczce, posortowanych od najlepszych.")
@app_commands.guild_only()
async def lista_paczka_command(interaction: discord.Interaction):
    """
    Wyświetla ranking kierowców dostępnych w paczkach, posortowanych po ocenie ogólnej.
    """
    global all_drivers_data, last_drivers_load_time

    # Przeładowanie danych kierowców, jeśli plik uległ zmianie
    if os.path.exists(DRIVERS_FILE):
        current_drivers_mtime = os.path.getmtime(DRIVERS_FILE)
        if current_drivers_mtime > last_drivers_load_time:
            print(f"Wykryto zmiany w {DRIVERS_FILE}. Przeładowuję dane kierowców...")
            all_drivers_data = load_drivers_data()
            last_drivers_load_time = current_drivers_mtime
    else:
        await interaction.response.send_message(
            "Wystąpił błąd: brak danych o kierowcach. Skontaktuj się z administratorem.",
            ephemeral=True
        )
        return

    if not all_drivers_data:
        await interaction.response.send_message(
            "Brak dostępnych kart kierowców do wyświetlenia. Skontaktuj się z administratorem.",
            ephemeral=True
        )
        return

    # Sortowanie kierowców malejąco po ocenie ogólnej
    sorted_drivers = sorted(all_drivers_data, key=lambda d: d.get('ocena_ogolna', 0), reverse=True)

    # Tworzenie listy do opisu embeda
    drivers_list = []
    for driver in sorted_drivers:
        ocena = driver.get('ocena_ogolna', 'Brak')
        drivers_list.append(f"{driver['kierowca']} - `{ocena}` OVR")
    
    description_text = "\n".join(drivers_list)

    embed = discord.Embed(
        title="Lista zawartości paczki",
        description=description_text,
        color=hex_color("#FFFFFF")
    )
    
    embed.set_footer(text="Official Polish Racing Fortnite")

    await interaction.response.send_message(embed=embed, ephemeral=False)

@tree.command(name="ranking", description="Wyświetla top 10 najbardziej wartościowych kont graczy.")
@app_commands.guild_only()
async def ranking_command(interaction: discord.Interaction):
    """
    Wyświetla ranking graczy na podstawie wartości ich kont (paczki, coinsy i karty).
    """
    global bot_data, last_data_reload_time, all_drivers_data, last_drivers_load_time

    # Upewnij się, że dane użytkowników są aktualne
    if os.path.exists(DB_FILE):
        current_file_mtime = os.path.getmtime(DB_FILE)
        if current_file_mtime > last_data_reload_time:
            bot_data = load_data()
            last_data_reload_time = current_file_mtime
            
    # Upewnij się, że dane kierowców są aktualne
    if os.path.exists(DRIVERS_FILE):
        current_drivers_mtime = os.path.getmtime(DRIVERS_FILE)
        if current_drivers_mtime > last_drivers_load_time:
            all_drivers_data = load_drivers_data()
            last_drivers_load_time = current_drivers_mtime

    # Definicja wartości punktowej: 1 paczka = 25 coinsów, 1 karta = 25 coinsów
    item_value = 25

    # Obliczanie wartości konta dla każdego użytkownika
    account_values = []
    for user_id_str, user_data in bot_data.items():
        coins = user_data.get("oprf_coins", 0)
        paczki = user_data.get("paczki", 0)
        karty = user_data.get("karty", [])
        
        # Całkowita wartość konta = coinsy + (paczki * wartość_paczki) + (liczba_kart * wartość_karty)
        total_value = coins + (paczki * item_value) + (len(karty) * item_value)
        
        # Przygotowanie listy kart do wyświetlenia w embedzie
        cards_display = ", ".join(karty) if karty else "Brak"
        
        account_values.append({
            "user_id": int(user_id_str),
            "user_name": user_data.get("user_name", "Nieznany Użytkownik"),
            "oprf_coins": coins,
            "paczki": paczki,
            "karty_display": cards_display,
            "total_value": total_value
        })

    # Sortowanie listy według wartości konta, malejąco
    sorted_accounts = sorted(account_values, key=lambda x: x["total_value"], reverse=True)

    # Tworzenie opisu embeda dla top 10
    description_lines = []
    for i, user in enumerate(sorted_accounts[:10]):
        # Użycie mentonu, jeśli użytkownik jest na serwerze
        try:
            member = interaction.guild.get_member(user["user_id"])
            user_display = member.mention if member else user["user_name"]
        except (AttributeError, KeyError):
            user_display = user["user_name"]
            
        description_lines.append(
            f"**{i + 1}**. {user_display} - `{user['paczki']}` paczek, `{user['oprf_coins']}` OPRF Coinsów, Karty: {user['karty_display']}"
        )
    
    description_text = "\n".join(description_lines)
    
    if not description_text:
        description_text = "Brak danych o kontach do wyświetlenia."

    embed = discord.Embed(
        title="Top 10 najbardziej wartościowych kont",
        description=description_text,
        color=hex_color("#FFFFFF")
    )
    
    if interaction.guild and interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    
    embed.set_footer(text="Official Polish Racing Fortnite")

    await interaction.response.send_message(embed=embed, ephemeral=False)

@tree.command(name="karta", description="Wyświetla posiadaną kartę.")
@app_commands.describe(nazwa="Nazwa kierowcy, którego kartę chcesz wyświetlić.")
@app_commands.guild_only()
async def karta_command(interaction: discord.Interaction, nazwa: str):
    """
    Wyświetla szczegóły karty kierowcy, jeśli użytkownik ją posiada.
    """
    user_id = interaction.user.id
    user_id_str = str(user_id)
    user_cards = get_user_cards(user_id)  # Ta funkcja przeładowuje dane użytkownika

    # Normalizuj wejście użytkownika, aby było case-insensitive
    nazwa_lower = nazwa.lower()
    
    # Przeładuj dane kierowców, jeśli są nieaktualne
    global all_drivers_data, last_drivers_load_time
    if os.path.exists(DRIVERS_FILE):
        current_drivers_mtime = os.path.getmtime(DRIVERS_FILE)
        if current_drivers_mtime > last_drivers_load_time:
            all_drivers_data = load_drivers_data()
            last_drivers_load_time = current_drivers_mtime

    # Sprawdź, czy użytkownik posiada kartę
    if nazwa not in user_cards:
        # Sprawdź również normalizowaną nazwę
        found = False
        for card_name in user_cards:
            if card_name.lower() == nazwa_lower:
                nazwa = card_name  # Użyj poprawnej nazwy z bazy danych
                found = True
                break
        
        if not found:
            await interaction.response.send_message(
                f"Nie posiadasz karty kierowcy o nazwie `{nazwa}`.",
                ephemeral=True
            )
            return

    # Znajdź dane kierowcy w globalnej liście
    driver_data = None
    for driver in all_drivers_data:
        if driver['kierowca'].lower() == nazwa_lower:
            driver_data = driver
            break

    if not driver_data:
        await interaction.response.send_message(
            f"Wystąpił błąd: nie znaleziono danych dla kierowcy `{nazwa}`. Skontaktuj się z administratorem.",
            ephemeral=True
        )
        return

    # Utwórz embed z danymi kierowcy
    card_embed = discord.Embed(
        title=f"Karta Kierowcy - {driver_data['kierowca']}",
        description=(
            f"**Informacje Kierowcy:**\n"
            f"`Numer` - #{driver_data['numer']}\n"
            f"`Drużyna` - {driver_data['druzyna']}\n"
            f"`Ocena Ogólna` - {driver_data['ocena_ogolna'] if driver_data.get('ocena_ogolna') is not None else 'Brak oceny'}"
        ),
        color=hex_color("#FFFFFF")
    )

    if 'link_thumbnail' in driver_data and driver_data['link_thumbnail']:
        card_embed.set_thumbnail(url=driver_data['link_thumbnail'])
    if 'link' in driver_data and driver_data['link']:
        card_embed.set_image(url=driver_data['link'])

    card_embed.set_footer(text="Official Polish Racing Fortnite")

    await interaction.response.send_message(embed=card_embed, ephemeral=False)
    
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
            "msg - bot wyśle wiadomość jaką będziesz chciał (tylko admin)\n"
            "`Ukośnik - /`\n"
            "pomoc - wyświetla kartę pomocy bota\n"
            "twitter - pozwala opublikować posta na kanale <#1282096776928559246>\n"
            "news - pozwala opublikować posta na kanale <#1228665355832922173> (tylko admin)\n"
            "rejestracja - udostępnia wynik rejestracji (tylko admin)\n"
            "kontrakt - wysyła kontrakt do FIA\n"
            "konto - wyświetla informacje o koncie\n"
            "sklep - pokazuje sklep OPRF\n"
            "paczka - otwiera paczkę kierowcy\n"
            "pitstop-game - udostępnia link do pobrania gry OPRF Pitstop Game\n"
            "lista-paczka - wyświetla co może znajdować się w paczce\n"
            "ranking - wyświetla top 10 najbogatszych kont biorąc pod uwagę ilość paczek, coinsów i karty\n"
            "karta - wyświetla posiadaną kartę\n"
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
