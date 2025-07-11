import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional
from datetime import datetime, timezone
import random
import json
import os

def hex_color(hex_str):
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

# Bazy danych json
DB_FILE = 'data.json' 
DRIVERS_FILE = 'drivers.json' 

def load_drivers_data():
    """
    Ładuje dane o kierowcach z pliku JSON. Zwraca pustą listę, jeśli plik nie istnieje.
    """
    if os.path.exists(DRIVERS_FILE):
        try:
            with open(DRIVERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ostrzeżenie: Plik {DRIVERS_FILE} jest uszkodzony lub pusty. Zwracam pustą listę.")
            return []
    return []

# Będziemy potrzebować globalnej zmiennej dla danych kierowców, podobnie jak dla bot_data
all_drivers_data = [] # Zostanie załadowana w on_ready

# Deklaracja globalnych zmiennych, które będą przechowywać dane i czas modyfikacji pliku.
# Zostaną one prawidłowo zainicjowane w funkcji on_ready bota.
bot_data = {}
last_data_reload_time = 0.0

def load_data():
    """
    Ładuje dane z pliku JSON. Zwraca pusty słownik, jeśli plik nie istnieje.
    Obsługuje błąd, jeśli plik jest pusty lub uszkodzony.
    """
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ostrzeżenie: Plik {DB_FILE} jest uszkodzony lub pusty. Zwracam pusty słownik.")
            return {}
    return {}

def save_data(data):
    """
    Zapisuje dane do pliku JSON. Plik jest formatowany z wcięciem (indent=4) dla lepszej czytelności.
    """
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Funkcje pomocnicze do pobierania danych użytkownika ---
# Te funkcje odwołują się do globalnej zmiennej bot_data
def get_user_coins(user_id):
    """Pobiera liczbę oprf_coins użytkownika."""
    user_id_str = str(user_id)
    return bot_data.get(user_id_str, {}).get("oprf_coins", 0) # Domyślnie 0, jeśli brak danych

def get_user_paczki(user_id):
    """Pobiera liczbę paczek użytkownika."""
    user_id_str = str(user_id)
    return bot_data.get(user_id_str, {}).get("paczki", 0)

def get_user_cards(user_id):
    """Pobiera listę kart kierowców użytkownika."""
    user_id_str = str(user_id)
    # Zapewnia, że pole 'karty' istnieje i zwraca pustą listę, jeśli go brak
    return bot_data.get(user_id_str, {}).get("karty", [])

    
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
    
    
@tree.command(name="sklep", description="Odwiedź sklep OPRF!")
@app_commands.guild_only()
async def sklep_command(interaction: discord.Interaction):
    thumbnail_url = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None

    # Stwórz przycisk
    buy_pack_button = discord.ui.Button(
        label="Kup paczkę Kierowców OPRF",
        style=discord.ButtonStyle.success,
        emoji="📦",
        custom_id="zakuppaczka" # Custom ID, które będziemy sprawdzać
    )

    # Stwórz View i dodaj do niego przycisk
    view = discord.ui.View(timeout=180) # Timeout określa, jak długo przyciski będą aktywne
    view.add_item(buy_pack_button)

    # --- Definicja funkcji callback dla przycisku wewnątrz funkcji komendy ---
    async def buy_pack_button_callback(interaction: discord.Interaction):
        user_id = interaction.user.id
        user_display_name = interaction.user.display_name

        # --- Przeładowanie danych (tak jak w /konto) ---
        global bot_data, last_data_reload_time
        if os.path.exists(DB_FILE):
            current_file_mtime = os.path.getmtime(DB_FILE)
            if current_file_mtime > last_data_reload_time:
                print(f"Wykryto zmiany w {DB_FILE}. Przeładowuję dane przed zakupem...")
                bot_data = load_data()
                last_data_reload_time = current_file_mtime
        else:
            if bot_data:
                bot_data = {}
                print(f"Plik {DB_FILE} nie istnieje. Zresetowano dane w pamięci.")
            last_data_reload_time = 0.0

        # Krok 2: Sprawdź, czy użytkownik ma wystarczająco monet
        item_cost = 5
        current_coins = get_user_coins(user_id)
        
        if current_coins >= item_cost:
            # Krok 3: Wykonaj transakcję
            new_coins = current_coins - item_cost
            new_paczki = get_user_paczki(user_id) + 1

            # Zaktualizuj dane w bot_data
            user_id_str = str(user_id)
            if user_id_str not in bot_data:
                bot_data[user_id_str] = {
                    "user_name": interaction.user.name,
                    "oprf_coins": 0,
                    "paczki": 0
                }
            bot_data[user_id_str]["oprf_coins"] = new_coins
            bot_data[user_id_str]["paczki"] = new_paczki
            
            save_data(bot_data)

            await interaction.response.send_message(
                f"**Gratulacje, {user_display_name}!** Pomyślnie zakupiono paczkę Kierowców OPRF. "
                f"Masz teraz `{new_coins}` OPRF Coinsów i `{new_paczki}` paczek.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"**{user_display_name}**, masz tylko `{current_coins}` OPRF Coinsów. Potrzebujesz `{item_cost}` monet, aby kupić paczkę.",
                ephemeral=True
            )
    
    # --- PRZYPISANIE FUNKCJI CALLBACK DO PRZYCISKU ---
    # To jest KLUCZOWY ELEMENT, który łączy przycisk z funkcją obsługującą jego kliknięcie.
    # Bez tej linii, przycisk nie będzie działać.
    buy_pack_button.callback = buy_pack_button_callback


    # Stwórz Embed
    embed = discord.Embed(
        title="Sklep OPRF 🛒",
        description="Witaj w sklepie discord Official Polish Racing Fortnite!\n"
                    "**Przedmioty**\n"
                    "- Paczka kierowców OPRF `5 OPRF Coins`",
        color=hex_color("#FFFFFF")
    )
    
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    
    embed.set_footer(text="Official Polish Racing Fortnite")

    # Wyślij wiadomość z Embedem i View
    await interaction.response.send_message(embed=embed, view=view)

    
@tree.command(name="konto", description="Wyświetla informacje o koncie!")
@app_commands.describe(member="Opcjonalnie: Użytkownik, którego konto chcesz sprawdzić.")
async def konto_command(interaction: discord.Interaction, member: discord.Member = None):
    # Dostęp do globalnych zmiennych, które mogą być modyfikowane
    global bot_data, last_data_reload_time

    # KROK 1: Sprawdź, czy plik JSON został zmodyfikowany od ostatniego odczytu
    if os.path.exists(DB_FILE):
        current_file_mtime = os.path.getmtime(DB_FILE) # Czas ostatniej modyfikacji pliku
        if current_file_mtime > last_data_reload_time:
            print(f"Wykryto zmiany w {DB_FILE}. Przeładowuję dane...")
            bot_data = load_data() # Przeładuj najnowsze dane z pliku
            last_data_reload_time = current_file_mtime # Zaktualizuj czas ostatniego przeładowania
    else:
        # Jeśli plik z jakiegoś powodu zniknął, zresetuj dane w pamięci
        if bot_data: # Tylko jeśli bot_data nie jest już puste
            bot_data = {}
            print(f"Plik {DB_FILE} nie istnieje. Zresetowano dane w pamięci.")
        last_data_reload_time = 0.0 # Zresetuj czas modyfikacji

    # KROK 2: Określ, dla kogo wyświetlamy konto
    target_user = member if member else interaction.user # Użytkownik docelowy (samemu sobie lub podany)
    user_id = target_user.id
    target_discord_username = target_user.name # Globalna nazwa użytkownika Discorda

    # KROK 3: Inicjalizacja danych dla użytkownika, jeśli ich jeszcze nie ma lub brakuje pola 'karty'
    user_id_str = str(user_id)
    if user_id_str not in bot_data:
        bot_data[user_id_str] = {
            "user_name": target_discord_username,
            "oprf_coins": 0,
            "paczki": 0,
            "karty": [] # WAŻNE: Inicjalizuj 'karty' jako pustą listę dla nowych użytkowników
        }
        save_data(bot_data)
    # Jeśli użytkownik istnieje, ale brakuje mu pola 'karty' (np. ze starego formatu danych)
    elif "karty" not in bot_data[user_id_str]:
        bot_data[user_id_str]["karty"] = []
        save_data(bot_data)


    # KROK 4: Pobierz aktualne wartości monet, paczek i KART
    coins = get_user_coins(user_id)
    paczki = get_user_paczki(user_id)
    karty = get_user_cards(user_id) # NOWE: Pobierz listę kart

    # Sformatuj listę kart do wyświetlenia
    if karty:
        cards_display = ", ".join(karty) # Połącz nazwy kart przecinkami
    else:
        cards_display = "Brak kart" # Jeśli lista jest pusta, wyświetl "Brak kart"

    # KROK 5: Przygotuj opis dla wiadomości Embed (ZMODYFIKOWANY)
    description_text = (
        f"**Stan Konta**\n"
        f"- Stan Konta: `{coins}` OPRF Coinsów\n"
        f"**Przedmioty**\n"
        f"- Paczki: `{paczki}`\n"
        f"- Karty: {cards_display}" # NOWE: Dodaj wyświetlanie kart
    )

    # KROK 6: Stwórz Embed z informacjami o koncie
    # Używamy .display_name dla lepszego wyświetlania na serwerze (np. nick z serwera, nie globalny)
    embed_title = f"Konto Użytkownika: {target_user.name}"
    
    # Upewnij się, że używasz funkcji hex_to_discord_color, jeśli tak ją nazwałeś.
    # W Twoim przykładzie jest hex_color, więc upewnię się, że to działa.
    embed = discord.Embed(
        title=embed_title,
        description=description_text,
        color=hex_color("#FFFFFF") # Zmieniłem na hex_to_discord_color dla spójności
    )

    # Ustaw awatar docelowego użytkownika
    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
    embed.set_footer(text="Official Polish Racing Fortnite")

    # KROK 7: Wyślij wiadomość (domyślnie publicznie, bo ephemeral_status = False)
    ephemeral_status = False 
    
    await interaction.response.send_message(embed=embed, ephemeral=ephemeral_status)

@tree.command(name="paczka", description="Wyświetla paczkę do otwarcia.")
@app_commands.guild_only()
async def paczka_command(interaction: discord.Interaction):
    # KROK 1: Sprawdź i przeładuj dane użytkownika
    global bot_data, last_data_reload_time
    if os.path.exists(DB_FILE):
        current_file_mtime = os.path.getmtime(DB_FILE)
        if current_file_mtime > last_data_reload_time:
            print(f"Wykryto zmiany w {DB_FILE}. Przeładowuję dane użytkownika przed otwarciem paczki...")
            bot_data = load_data()
            last_data_reload_time = current_file_mtime
    else:
        if bot_data:
            bot_data = {}
            print(f"Plik {DB_FILE} nie istnieje. Zresetowano dane użytkownika.")
        last_data_reload_time = 0.0

    user_id = interaction.user.id
    current_paczki = get_user_paczki(user_id)

    if current_paczki < 1:
        await interaction.response.send_message(
            "Nie masz żadnych paczek do otwarcia! Kup je w `/sklep`.",
            ephemeral=True
        )
        return

    # KROK 2: Stwórz przycisk "Otwórz Paczkę"
    open_pack_button = discord.ui.Button(
        label="Otwórz Paczkę",
        style=discord.ButtonStyle.success,
        emoji="📦",
        custom_id="paczkaopen"
    )

    # KROK 3: Stwórz View i dodaj przycisk
    view = discord.ui.View(timeout=180)
    view.add_item(open_pack_button)

    # KROK 4: Definiuj funkcję callback dla przycisku "Otwórz Paczkę"
    async def open_pack_button_callback(interaction: discord.Interaction):
        # This function is executed when the button is clicked
        user_id = interaction.user.id
        user_display_name = interaction.user.display_name # user_display_name IS DEFINED HERE!

        # --- Ponowne przeładowanie danych użytkownika przed transakcją (bezpieczeństwo) ---
        global bot_data, last_data_reload_time
        if os.path.exists(DB_FILE):
            current_file_mtime = os.path.getmtime(DB_FILE)
            if current_file_mtime > last_data_reload_time:
                print(f"Wykryto zmiany w {DB_FILE}. Przeładowuję dane użytkownika przed otwarciem paczki...")
                bot_data = load_data()
                last_data_reload_time = current_file_mtime
        else:
            if bot_data:
                bot_data = {}
                print(f"Plik {DB_FILE} nie istnieje. Zresetowano dane w pamięci.")
            last_data_reload_time = 0.0

        current_paczki_after_check = get_user_paczki(user_id)

        if current_paczki_after_check < 1:
            await interaction.response.send_message(
                "Wygląda na to, że nie masz już paczek! Być może właśnie ją otworzyłeś.",
                ephemeral=True
            )
            return

        # KROK 5: Odejmij paczkę od użytkownika
        user_id_str = str(user_id)
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

        # KROK 6: Sprawdź i przeładuj dane kierowców (jeśli plik się zmienił)
        global all_drivers_data
        if os.path.exists(DRIVERS_FILE):
            current_drivers_mtime = os.path.getmtime(DRIVERS_FILE)
            if not all_drivers_data or current_drivers_mtime > getattr(paczka_command, '_last_drivers_load_time', 0):
                 print(f"Wykryto zmiany w {DRIVERS_FILE}. Przeładowuję dane kierowców...")
                 all_drivers_data = load_drivers_data()
                 paczka_command._last_drivers_load_time = current_drivers_mtime 
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

        # KROK 7: Wylosuj losowego kierowcę
        chosen_driver = random.choice(all_drivers_data)

        # KROK 8: Dodaj wylosowaną kartę do listy kart użytkownika
        bot_data[user_id_str]["karty"].append(chosen_driver['kierowca'])

        # --- ZAPISUJEMY ZMODYFIKOWANE DANE ---
        save_data(bot_data)

        # KROK 9: Stwórz Embed z informacjami o wylosowanym kierowcy (publiczny)
        reward_embed = discord.Embed(
            title=f"Karta Kierowcy - {chosen_driver['kierowca']}",
            description=(
                f"**Informacje Kierowcy:**\n"
                f"`Numer` - #{chosen_driver['numer']}\n"
                f"`Drużyna` - {chosen_driver['druzyna']}\n"
                f"`Ocena Ogólna` - {chosen_driver['ocena_ogolna']}"
            ),
            color=hex_color("#FFFFFF")
        )
        
        if 'link_thumbnail' in chosen_driver and chosen_driver['link_thumbnail']:
            reward_embed.set_thumbnail(url=chosen_driver['link_thumbnail'])
        if 'link' in chosen_driver and chosen_driver['link']:
            reward_embed.set_image(url=chosen_driver['link'])

        reward_embed.set_author(
            name=f"Otwarte przez - {user_display_name}", # Correctly use user_display_name here
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        reward_embed.set_footer(text="Official Polish Racing Fortnite")

        # The 'content' part here is for the reward message, which IS inside the callback
        await interaction.response.send_message(
            content=f"**{user_display_name}** otworzył paczkę i wylosował:", # This is fine!
            embed=reward_embed,
            ephemeral=False
        )


    # KROK 5 (ponownie): Przypisz callback do przycisku
    open_pack_button.callback = open_pack_button_callback

    # KROK 6: Stwórz początkowy Embed "Paczka 📦"
    initial_embed = discord.Embed(
        title="Paczka 📦",
        description="Twoja paczka stoi przed tobą \ni czeka aż ją otworzysz!",
        color=hex_color("#FFFFFF")
    )
    initial_embed.set_image(url="https://cdn.discordapp.com/attachments/1246818926604582984/1387580177017602090/zlota_paczka.png?ex=685ddc3e&is=685c8abe&hm=f557af444b25babb8385b5e3be6fa617bae30e12a65b47114e0ed9b7e9c4787e&")
    initial_embed.set_footer(text="Official Polish Racing Fortnite")

    # KROK 7: Wyślij początkową wiadomość z Embedem i przyciskiem
    # This message is sent BEFORE the button is clicked, so user_display_name is not available here.
    # We remove the 'content' argument that caused the error.
    await interaction.response.send_message(embed=initial_embed, view=view, ephemeral=False)

    
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
            "konto - wyświetla informacje o koncie\n"
            "sklep - pokazuje sklep OPRF\n"
            "paczka - otwiera paczkę kierowców\n"
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
