import os
import sqlite3
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    BotCommandScopeDefault,
)

# ============================================================
# BRAWL STARS ARENA — FINAL
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()

ADMIN_IDS = set()

if ADMIN_ID_RAW:
    for item in ADMIN_ID_RAW.split(","):
        item = item.strip()
        if item.isdigit():
            ADMIN_IDS.add(int(item))

DB_FILE = "arena.db"

db = sqlite3.connect(DB_FILE, check_same_thread=False)
db.row_factory = sqlite3.Row

db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA foreign_keys=ON")
db.commit()

bot = Bot(TOKEN)
dp = Dispatcher()


# ============================================================
# DATABASE
# ============================================================

db.executescript("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT DEFAULT '',
    language TEXT DEFAULT 'ru',
    nickname TEXT DEFAULT '',
    player_id TEXT DEFAULT '',
    country TEXT DEFAULT '',
    rating INTEGER DEFAULT 1000,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    reg_step TEXT DEFAULT '',
    temp_nickname TEXT DEFAULT '',
    temp_player_id TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    captain_id INTEGER NOT NULL,
    rating INTEGER DEFAULT 1000,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    created_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS team_members (
    team_id INTEGER NOT NULL,
    telegram_id INTEGER NOT NULL,
    UNIQUE(team_id, telegram_id)
);

CREATE TABLE IF NOT EXISTS tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mode TEXT NOT NULL,
    prize TEXT DEFAULT '',
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'open',
    max_players INTEGER DEFAULT 0,
    created_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    telegram_id INTEGER NOT NULL,
    team_id INTEGER DEFAULT NULL,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT '',
    UNIQUE(tournament_id, telegram_id)
);

CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT DEFAULT ''
);
""")

db.commit()


# ============================================================
# TEXTS
# ============================================================

TEXTS = {

    "ru": {

        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Добро пожаловать на арену!\n\n"
            "⚔️ Турниры • 👥 Команды • 📊 Рейтинг\n"
            "🔥 Честная игра. Жёсткая конкуренция.",

        "tournaments": "🏆 Турниры",
        "profile": "👤 Профиль",
        "ranking": "📊 Рейтинг",
        "team": "👥 Команда",
        "news": "📰 Новости",
        "settings": "⚙️ Настройки",
        "help": "❓ Помощь",
        "rules": "📜 Правила",
        "register": "📝 Регистрация",
        "statistics": "📈 Статистика",

        "one_vs_one": "🥊 1v1",
        "three_vs_three": "👥 3v3",

        "my_applications": "📋 Мои заявки",
        "active_tournaments": "🔥 Активные турниры",

        "create_team": "➕ Создать команду",
        "my_team": "👥 Моя команда",
        "invites": "🔗 Приглашения",

        "players": "🥇 Игроки",
        "teams": "👥 Команды",

        "language": "🌐 Язык",

        "back": "⬅️ Назад",
        "home": "🏠 Главное меню",

        "choose_language":
            "🌐 Выбери язык:",

        "not_registered":
            "👤 Профиль ещё не создан.\n\n"
            "Нажми «📝 Регистрация».",

        "already_registered":
            "Ты уже зарегистрирован.",

        "ask_nickname":
            "🎮 Введи свой ник в Brawl Stars:",

        "ask_player_id":
            "🆔 Введи свой Player ID:",

        "ask_country":
            "🌎 Введи свою страну:",

        "registration_done":
            "🔥 РЕГИСТРАЦИЯ ЗАВЕРШЕНА!\n\n"
            "Добро пожаловать в Arena.\n\n"
            "⭐ Стартовый рейтинг: 1000\n"
            "🎯 Уровень: 1\n"
            "💎 XP: 0",

        "no_tournaments":
            "🏆 Сейчас открытых турниров нет.\n\n"
            "Следи за новостями Arena.",

        "no_news":
            "📰 Новостей пока нет.",

        "no_applications":
            "📋 У тебя пока нет заявок.",

        "settings_text":
            "⚙️ НАСТРОЙКИ\n\n"
            "Выбери язык интерфейса.",

        "help_text":
            "❓ ПОМОЩЬ\n\n"
            "🏆 Турниры — участие в соревнованиях.\n"
            "👤 Профиль — твой профиль и статистика.\n"
            "📊 Рейтинг — топ игроков и команд.\n"
            "👥 Команда — создание команды 3v3.\n"
            "📰 Новости — события Arena.\n\n"
            "Если возникла проблема — обратись к администрации.",

        "rules_text":
            "📜 ПРАВИЛА BRAWL STARS ARENA\n\n"
            "1. Читы и сторонние программы запрещены.\n"
            "2. Запрещена подмена результатов.\n"
            "3. Оскорбления и токсичное поведение запрещены.\n"
            "4. Запрещены договорные результаты.\n"
            "5. Решение администрации по спорным ситуациям окончательное.\n"
            "6. Нарушение правил может привести к дисквалификации.\n\n"
            "🔥 Играем честно. Побеждает сильнейший.",

        "team_empty":
            "👥 У тебя пока нет команды.\n\n"
            "Создай команду для участия в 3v3.",

        "team_created":
            "👥 Команда создана!\n\n"
            "Теперь пригласи ещё двух игроков.",

        "ranking_empty":
            "📊 Пока недостаточно данных для рейтинга.",

        "admin_only":
            "🛡️ Эта функция доступна только администрации."
    },


    "en": {

        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Welcome to the arena!\n\n"
            "⚔️ Tournaments • 👥 Teams • 📊 Rankings\n"
            "🔥 Fair play. Serious competition.",

        "tournaments": "🏆 Tournaments",
        "profile": "👤 Profile",
        "ranking": "📊 Ranking",
        "team": "👥 Team",
        "news": "📰 News",
        "settings": "⚙️ Settings",
        "help": "❓ Help",
        "rules": "📜 Rules",
        "register": "📝 Registration",
        "statistics": "📈 Statistics",

        "one_vs_one": "🥊 1v1",
        "three_vs_three": "👥 3v3",

        "my_applications": "📋 My Applications",
        "active_tournaments": "🔥 Active Tournaments",

        "create_team": "➕ Create Team",
        "my_team": "👥 My Team",
        "invites": "🔗 Invitations",

        "players": "🥇 Players",
        "teams": "👥 Teams",

        "language": "🌐 Language",

        "back": "⬅️ Back",
        "home": "🏠 Main Menu",

        "choose_language":
            "🌐 Choose your language:",

        "not_registered":
            "👤 Your profile is not created yet.\n\n"
            "Press «📝 Registration».",

        "already_registered":
            "You are already registered.",

        "ask_nickname":
            "🎮 Enter your Brawl Stars nickname:",

        "ask_player_id":
            "🆔 Enter your Player ID:",

        "ask_country":
            "🌎 Enter your country:",

        "registration_done":
            "🔥 REGISTRATION COMPLETE!\n\n"
            "Welcome to Arena.\n\n"
            "⭐ Starting rating: 1000\n"
            "🎯 Level: 1\n"
            "💎 XP: 0",

        "no_tournaments":
            "🏆 There are no open tournaments right now.",

        "no_news":
            "📰 No news yet.",

        "no_applications":
            "📋 You have no applications yet.",

        "settings_text":
            "⚙️ SETTINGS\n\n"
            "Choose your interface language.",

        "help_text":
            "❓ HELP\n\n"
            "🏆 Tournaments — join competitions.\n"
            "👤 Profile — your profile and stats.\n"
            "📊 Ranking — players and teams.\n"
            "👥 Team — create a 3v3 team.\n"
            "📰 News — Arena events.",

        "rules_text":
            "📜 BRAWL STARS ARENA RULES\n\n"
            "1. Cheats and third-party programs are forbidden.\n"
            "2. Fake results are forbidden.\n"
            "3. Insults and toxic behavior are forbidden.\n"
            "4. Match fixing is forbidden.\n"
            "5. Admin decisions are final.\n"
            "6. Violations may result in disqualification.",

        "team_empty":
            "👥 You don't have a team yet.\n\n"
            "Create one for 3v3.",

        "team_created":
            "👥 Team created!\n\n"
            "Now invite two more players.",

        "ranking_empty":
            "📊 Not enough data for the ranking yet.",

        "admin_only":
            "🛡️ This feature is for administrators only."
    },


    "uz": {

        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Arenaga xush kelibsiz!\n\n"
            "⚔️ Turnirlar • 👥 Jamoalar • 📊 Reyting\n"
            "🔥 Halol o‘yin. Kuchli raqobat.",

        "tournaments": "🏆 Turnirlar",
        "profile": "👤 Profil",
        "ranking": "📊 Reyting",
        "team": "👥 Jamoa",
        "news": "📰 Yangiliklar",
        "settings": "⚙️ Sozlamalar",
        "help": "❓ Yordam",
        "rules": "📜 Qoidalar",
        "register": "📝 Ro‘yxatdan o‘tish",
        "statistics": "📈 Statistika",

        "one_vs_one": "🥊 1v1",
        "three_vs_three": "👥 3v3",

        "my_applications": "📋 Arizalarim",
        "active_tournaments": "🔥 Faol turnirlar",

        "create_team": "➕ Jamoa yaratish",
        "my_team": "👥 Mening jamoam",
        "invites": "🔗 Takliflar",

        "players": "🥇 O‘yinchilar",
        "teams": "👥 Jamoalar",

        "language": "🌐 Til",

        "back": "⬅️ Orqaga",
        "home": "🏠 Bosh menyu",

        "choose_language":
            "🌐 Tilni tanlang:",

        "not_registered":
            "👤 Profilingiz hali yaratilmagan.\n\n"
            "«📝 Ro‘yxatdan o‘tish» tugmasini bosing.",

        "already_registered":
            "Siz allaqachon ro‘yxatdan o‘tgansiz.",

        "ask_nickname":
            "🎮 Brawl Stars nikkingizni kiriting:",

        "ask_player_id":
            "🆔 Player ID ni kiriting:",

        "ask_country":
            "🌎 Davlatingizni kiriting:",

        "registration_done":
            "🔥 RO‘YXATDAN O‘TISH YAKUNLANDI!\n\n"
            "Arena'ga xush kelibsiz.\n\n"
            "⭐ Boshlang‘ich reyting: 1000\n"
            "🎯 Daraja: 1\n"
            "💎 XP: 0",

        "no_tournaments":
            "🏆 Hozircha ochiq turnirlar yo‘q.",

        "no_news":
            "📰 Hozircha yangiliklar yo‘q.",

        "no_applications":
            "📋 Sizda hali arizalar yo‘q.",

        "settings_text":
            "⚙️ SOZLAMALAR\n\n"
            "Interfeys tilini tanlang.",

        "help_text":
            "❓ YORDAM\n\n"
            "🏆 Turnirlar — musobaqalarda qatnashing.\n"
            "👤 Profil — profil va statistika.\n"
            "📊 Reyting — o‘yinchilar va jamoalar.\n"
            "👥 Jamoa — 3v3 jamoa yarating.\n"
            "📰 Yangiliklar — Arena voqealari.",

        "rules_text":
            "📜 ARENA QOIDALARI\n\n"
            "1. Cheat va begona dasturlar taqiqlangan.\n"
            "2. Soxta natijalar taqiqlangan.\n"
            "3. Haqorat va toksik xatti-harakatlar taqiqlangan.\n"
            "4. Kelishilgan natijalar taqiqlangan.\n"
            "5. Admin qarori yakuniy.\n"
            "6. Qoidabuzarlik diskvalifikatsiyaga olib kelishi mumkin.",

        "team_empty":
            "👥 Sizda hali jamoa yo‘q.\n\n"
            "3v3 uchun jamoa yarating.",

        "team_created":
            "👥 Jamoa yaratildi!\n\n"
            "Endi yana ikki o‘yinchini taklif qiling.",

        "ranking_empty":
            "📊 Reyting uchun ma’lumot yetarli emas.",

        "admin_only":
            "🛡️ Bu funksiya faqat administratorlar uchun."
    },


    "pt": {

        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Bem-vindo à arena!\n\n"
            "⚔️ Torneios • 👥 Equipes • 📊 Rankings\n"
            "🔥 Jogo limpo. Competição séria.",

        "tournaments": "🏆 Torneios",
        "profile": "👤 Perfil",
        "ranking": "📊 Ranking",
        "team": "👥 Equipe",
        "news": "📰 Notícias",
        "settings": "⚙️ Configurações",
        "help": "❓ Ajuda",
        "rules": "📜 Regras",
        "register": "📝 Registro",
        "statistics": "📈 Estatísticas",

        "one_vs_one": "🥊 1v1",
        "three_vs_three": "👥 3v3",

        "my_applications": "📋 Minhas inscrições",
        "active_tournaments": "🔥 Torneios ativos",

        "create_team": "➕ Criar equipe",
        "my_team": "👥 Minha equipe",
        "invites": "🔗 Convites",

        "players": "🥇 Jogadores",
        "teams": "👥 Equipes",

        "language": "🌐 Idioma",

        "back": "⬅️ Voltar",
        "home": "🏠 Menu Principal",

        "choose_language":
            "🌐 Escolha seu idioma:",

        "not_registered":
            "👤 Seu perfil ainda não foi criado.\n\n"
            "Pressione «📝 Registro».",

        "already_registered":
            "Você já está registrado.",

        "ask_nickname":
            "🎮 Digite seu apelido no Brawl Stars:",

        "ask_player_id":
            "🆔 Digite seu Player ID:",

        "ask_country":
            "🌎 Digite seu país:",

        "registration_done":
            "🔥 REGISTRO CONCLUÍDO!\n\n"
            "Bem-vindo à Arena.\n\n"
            "⭐ Rating inicial: 1000\n"
            "🎯 Nível: 1\n"
            "💎 XP: 0",

        "no_tournaments":
            "🏆 Não há torneios abertos no momento.",

        "no_news":
            "📰 Ainda não há notícias.",

        "no_applications":
            "📋 Você ainda não possui inscrições.",

        "settings_text":
            "⚙️ CONFIGURAÇÕES\n\n"
            "Escolha o idioma da interface.",

        "help_text":
            "❓ AJUDA\n\n"
            "🏆 Torneios — participe das competições.\n"
            "👤 Perfil — seu perfil e estatísticas.\n"
            "📊 Ranking — jogadores e equipes.\n"
            "👥 Equipe — crie uma equipe 3v3.\n"
            "📰 Notícias — eventos da Arena.",

        "rules_text":
            "📜 REGRAS DA ARENA\n\n"
            "1. Cheats e programas de terceiros são proibidos.\n"
            "2. Resultados falsos são proibidos.\n"
            "3. Ofensas e comportamento tóxico são proibidos.\n"
            "4. Resultados combinados são proibidos.\n"
            "5. A decisão da administração é final.\n"
            "6. Violações podem causar desclassificação.",

        "team_empty":
            "👥 Você ainda não possui uma equipe.\n\n"
            "Crie uma para 3v3.",

        "team_created":
            "👥 Equipe criada!\n\n"
            "Agora convide mais dois jogadores.",

        "ranking_empty":
            "📊 Ainda não há dados suficientes.",

        "admin_only":
            "🛡️ Esta função é apenas para administradores."
    }
}


# ============================================================
# SAFE TRANSLATION
# ============================================================

def T(lang, key, fallback=None):

    if lang not in TEXTS:
        lang = "ru"

    value = TEXTS[lang].get(key)

    if value:
        return value

    if fallback:
        return fallback

    return TEXTS["ru"].get(key, key)


# ============================================================
# USER FUNCTIONS
# ============================================================

def ensure_user(user):

    db.execute(
        """
        INSERT OR IGNORE INTO users
        (
            telegram_id,
            username,
            language,
            created_at
        )
        VALUES (?, ?, 'ru', ?)
        """,
        (
            user.id,
            user.username or "",
            datetime.utcnow().isoformat()
        )
    )

    db.execute(
        """
        UPDATE users
        SET username = ?
        WHERE telegram_id = ?
        """,
        (
            user.username or "",
            user.id
        )
    )

    db.commit()


def get_language(user_id):

    row = db.execute(
        """
        SELECT language
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    ).fetchone()

    if not row:
        return "ru"

    lang = row["language"]

    if lang not in TEXTS:
        return "ru"

    return lang


def set_language(user_id, lang):

    if lang not in TEXTS:
        lang = "ru"

    db.execute(
        """
        UPDATE users
        SET language = ?
        WHERE telegram_id = ?
        """,
        (
            lang,
            user_id
        )
    )

    db.commit()


def is_registered(user_id):

    row = db.execute(
        """
        SELECT nickname
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    ).fetchone()

    return bool(row and row["nickname"])


def is_admin(user_id):

    return user_id in ADMIN_IDS


def set_state(
    user_id,
    step,
    nickname="",
    player_id=""
):

    db.execute(
        """
        UPDATE users
        SET
            reg_step = ?,
            temp_nickname = ?,
            temp_player_id = ?
        WHERE telegram_id = ?
        """,
        (
            step,
            nickname,
            player_id,
            user_id
        )
    )

    db.commit()


def get_state(user_id):

    row = db.execute(
        """
        SELECT
            reg_step,
            temp_nickname,
            temp_player_id
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    ).fetchone()

    if not row:
        return "", "", ""

    return (
        row["reg_step"],
        row["temp_nickname"],
        row["temp_player_id"]
    )


def reset_state(user_id):

    db.execute(
        """
        UPDATE users
        SET
            reg_step = '',
            temp_nickname = '',
            temp_player_id = ''
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    db.commit()


# ============================================================
# KEYBOARDS
# ============================================================

def language_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data="lang_ru"
                ),
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data="lang_en"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇺🇿 O‘zbek",
                    callback_data="lang_uz"
                ),
                InlineKeyboardButton(
                    text="🇧🇷 Português",
                    callback_data="lang_pt"
                )
            ]
        ]
    )


def main_menu(lang):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text=T(lang, "tournaments"),
                    callback_data="tournaments"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "profile"),
                    callback_data="profile"
                ),
                InlineKeyboardButton(
                    text=T(lang, "ranking"),
                    callback_data="ranking"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "team"),
                    callback_data="team"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "news"),
                    callback_data="news"
                ),
                InlineKeyboardButton(
                    text=T(lang, "settings"),
                    callback_data="settings"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "help"),
                    callback_data="help"
                ),
                InlineKeyboardButton(
                    text=T(lang, "rules"),
                    callback_data="rules"
                )
            ]
        ]
    )


def back_keyboard(lang, callback_data="home"):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=T(lang, "back"),
                    callback_data=callback_data
                )
            ]
        ]
    )


def profile_keyboard(lang):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text=T(lang, "register"),
                    callback_data="register"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "statistics"),
                    callback_data="statistics"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "home"),
                    callback_data="home"
                )
            ]
        ]
    )


def tournament_keyboard(lang):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text=T(lang, "one_vs_one"),
                    callback_data="tour_1v1"
                ),
                InlineKeyboardButton(
                    text=T(lang, "three_vs_three"),
                    callback_data="tour_3v3"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "active_tournaments"),
                    callback_data="active_tournaments"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "my_applications"),
                    callback_data="my_applications"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "home"),
                    callback_data="home"
                )
            ]
        ]
    )


def ranking_keyboard(lang):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text=T(lang, "players"),
                    callback_data="player_ranking"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "teams"),
                    callback_data="team_ranking"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "home"),
                    callback_data="home"
                )
            ]
        ]
    )


def team_keyboard(lang):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text=T(lang, "create_team"),
                    callback_data="create_team"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "my_team"),
                    callback_data="my_team"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "invites"),
                    callback_data="team_invites"
                )
            ],

            [
                InlineKeyboardButton(
                    text=T(lang, "home"),
                    callback_data="home"
                )
            ]
        ]
    )


# ============================================================
# TELEGRAM COMMAND MENU
# ============================================================

async def setup_commands():

    commands = [

        BotCommand(
            command="start",
            description="🏠 Главная"
        ),

        BotCommand(
            command="profile",
            description="👤 Профиль"
        ),

        BotCommand(
            command="tournaments",
            description="🏆 Турниры"
        ),

        BotCommand(
            command="ranking",
            description="📊 Рейтинг"
        ),

        BotCommand(
            command="team",
            description="👥 Команда"
        ),

        BotCommand(
            command="news",
            description="📰 Новости"
        ),

        BotCommand(
            command="help",
            description="❓ Помощь"
        )
    ]

    await bot.set_my_commands(
        commands,
        scope=BotCommandScopeDefault()
    )


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def start_handler(message: types.Message):

    ensure_user(message.from_user)

    reset_state(message.from_user.id)

    await message.answer(
        "🏆 BRAWL STARS ARENA\n\n"
        "🔥 Добро пожаловать на арену!\n\n"
        "⚔️ Турниры\n"
        "👥 Команды\n"
        "📊 Рейтинг\n"
        "🏆 Соревнования\n\n"
        "🌎 Выбери язык / Choose your language:",
        reply_markup=language_keyboard()
    )


# ============================================================
# HOME
# ============================================================

@dp.callback_query(lambda c: c.data == "home")
async def home_handler(callback: types.CallbackQuery):

    ensure_user(callback.from_user)

    reset_state(callback.from_user.id)

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        T(lang, "welcome"),
        reply_markup=main_menu(lang)
    )

    await callback.answer()


# ============================================================
# LANGUAGE
# ============================================================

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def language_handler(callback: types.CallbackQuery):

    ensure_user(callback.from_user)

    lang = callback.data.replace("lang_", "")

    if lang not in TEXTS:
        lang = "ru"

    set_language(
        callback.from_user.id,
        lang
    )

    await callback.message.edit_text(
        T(lang, "welcome"),
        reply_markup=main_menu(lang)
    )

    await callback.answer()


# ============================================================
# SETTINGS
# ============================================================

@dp.callback_query(lambda c: c.data == "settings")
async def settings_handler(callback: types.CallbackQuery):

    ensure_user(callback.from_user)

    lang = get_language(callback.from_user.id)

    # FIX FOR KeyError: 'language'
    language_text = T(
        lang,
        "language",
        "🌐 Language"
    )

    settings_text = T(
        lang,
        "settings_text",
        "⚙️ Settings"
    )

    home_text = T(
        lang,
        "home",
        "🏠 Main Menu"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text=language_text,
                    callback_data="language"
                )
            ],

            [
                InlineKeyboardButton(
                    text=home_text,
                    callback_data="home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        settings_text,
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "language")
async def language_settings_handler(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "🌐 Выбери язык / Choose your language:",
        reply_markup=language_keyboard()
    )

    await callback.answer()


# ============================================================
# PROFILE
# ============================================================

async def show_profile(target, user_id):

    ensure_user(target.from_user)

    lang = get_language(user_id)

    row = db.execute(
        """
        SELECT
            nickname,
            player_id,
            country,
            rating,
            wins,
            losses,
            streak,
            best_streak,
            level,
            xp
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    ).fetchone()

    if not row or not row["nickname"]:

        text = T(
            lang,
            "not_registered"
        )

    else:

        total = row["wins"] + row["losses"]

        winrate = (
            round(row["wins"] * 100 / total)
            if total
            else 0
        )

        text = (
            "👤 PROFILE\n\n"
            f"🎮 Ник: {row['nickname']}\n"
            f"🆔 Player ID: {row['player_id']}\n"
            f"🌎 Страна: {row['country']}\n\n"
            f"⭐ Рейтинг: {row['rating']}\n"
            f"🎯 Уровень: {row['level']}\n"
            f"💎 XP: {row['xp']}\n"
            f"🏆 Победы: {row['wins']}\n"
            f"❌ Поражения: {row['losses']}\n"
            f"📊 Winrate: {winrate}%\n"
            f"🔥 Серия: {row['streak']}\n"
            f"💎 Лучшая серия: {row['best_streak']}"
        )

    keyboard = profile_keyboard(lang)

    if isinstance(target, types.CallbackQuery):
        await target.message.edit_text(
            text,
            reply_markup=keyboard
        )
    else:
        await target.answer(
            text,
            reply_markup=keyboard
        )


@dp.callback_query(lambda c: c.data == "profile")
async def profile_handler(callback: types.CallbackQuery):

    await show_profile(
        callback,
        callback.from_user.id
    )

    await callback.answer()


@dp.message(Command("profile"))
async def profile_command(message: types.Message):

    ensure_user(message.from_user)

    await show_profile(
        message,
        message.from_user.id
    )


# ============================================================
# REGISTRATION
# ============================================================

@dp.callback_query(lambda c: c.data == "register")
async def register_handler(callback: types.CallbackQuery):

    ensure_user(callback.from_user)

    user_id = callback.from_user.id

    lang = get_language(user_id)

    if is_registered(user_id):

        await callback.answer(
            T(lang, "already_registered"),
            show_alert=True
        )

        return

    set_state(
        user_id,
        "nickname"
    )

    await callback.message.edit_text(
        T(lang, "ask_nickname")
    )

    await callback.answer()


# ============================================================
# STATISTICS
# ============================================================

@dp.callback_query(lambda c: c.data == "statistics")
async def statistics_handler(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    lang = get_language(user_id)

    row = db.execute(
        """
        SELECT
            nickname,
            rating,
            wins,
            losses,
            streak,
            best_streak,
            level,
            xp
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    ).fetchone()

    if not row or not row["nickname"]:

        text = T(
            lang,
            "not_registered"
        )

    else:

        total = row["wins"] + row["losses"]

        winrate = (
            round(row["wins"] * 100 / total)
            if total
            else 0
        )

        text = (
            "📈 STATISTICS\n\n"
            f"🎮 {row['nickname']}\n\n"
            f"⭐ Rating: {row['rating']}\n"
            f"🎯 Level: {row['level']}\n"
            f"💎 XP: {row['xp']}\n"
            f"🏆 Wins: {row['wins']}\n"
            f"❌ Losses: {row['losses']}\n"
            f"🎮 Matches: {total}\n"
            f"📊 Winrate: {winrate}%\n"
            f"🔥 Streak: {row['streak']}\n"
            f"💎 Best streak: {row['best_streak']}"
        )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard(
            lang,
            "profile"
        )
    )

    await callback.answer()


# ============================================================
# TOURNAMENTS
# ============================================================

@dp.callback_query(lambda c: c.data == "tournaments")
async def tournaments_handler(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        "🏆 BRAWL STARS ARENA\n\n"
        "Выбери формат турнира:",
        reply_markup=tournament_keyboard(lang)
    )

    await callback.answer()


async def show_tournaments(
    callback,
    mode
):

    user_id = callback.from_user.id

    lang = get_language(user_id)

    rows = db.execute(
        """
        SELECT
            id,
            name,
            prize,
            description,
            max_players
        FROM tournaments
        WHERE mode = ?
        AND status = 'open'
        ORDER BY id DESC
        """,
        (mode,)
    ).fetchall()

    if not rows:

        await callback.message.edit_text(
            f"🏆 {mode}\n\n"
            f"{T(lang, 'no_tournaments')}",
            reply_markup=back_keyboard(
                lang,
                "tournaments"
            )
        )

        await callback.answer()

        return

    text = f"🏆 {mode}\n\n"

    buttons = []

    for row in rows:

        text += (
            f"🔥 {row['name']}\n"
            f"🎁 Приз: {row['prize'] or '—'}\n"
            f"👤 Лимит: "
            f"{row['max_players'] or '∞'}\n"
            f"ℹ️ {row['description'] or '—'}\n\n"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📝 {row['name']}",
                    callback_data=f"join_{row['id']}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text=T(lang, "back"),
                callback_data="tournaments"
            )
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "tour_1v1")
async def tournament_1v1(callback: types.CallbackQuery):

    await show_tournaments(
        callback,
        "1v1"
    )


@dp.callback_query(lambda c: c.data == "tour_3v3")
async def tournament_3v3(callback: types.CallbackQuery):

    await show_tournaments(
        callback,
        "3v3"
    )


@dp.callback_query(lambda c: c.data == "active_tournaments")
async def active_tournaments(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    rows = db.execute(
        """
        SELECT
            name,
            mode,
            prize
        FROM tournaments
        WHERE status = 'open'
        ORDER BY id DESC
        """
    ).fetchall()

    if not rows:

        text = T(
            lang,
            "no_tournaments"
        )

    else:

        text = "🔥 ACTIVE TOURNAMENTS\n\n"

        for row in rows:

            text += (
                f"🏆 {row['name']}\n"
                f"🎮 {row['mode']}\n"
                f"🎁 {row['prize'] or '—'}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard(
            lang,
            "tournaments"
        )
    )

    await callback.answer()


# ============================================================
# JOIN TOURNAMENT
# ============================================================

@dp.callback_query(
    lambda c:
        c.data.startswith("join_")
        and c.data[5:].isdigit()
)
async def join_tournament(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    lang = get_language(user_id)

    if not is_registered(user_id):

        await callback.answer(
            T(lang, "not_registered"),
            show_alert=True
        )

        return

    tournament_id = int(
        callback.data[5:]
    )

    tournament = db.execute(
        """
        SELECT
            id,
            name,
            mode,
            max_players,
            status
        FROM tournaments
        WHERE id = ?
        """,
        (tournament_id,)
    ).fetchone()

    if not tournament:

        await callback.answer(
            "Турнир не найден.",
            show_alert=True
        )

        return

    if tournament["status"] != "open":

        await callback.answer(
            "Турнир закрыт.",
            show_alert=True
        )

        return

    exists = db.execute(
        """
        SELECT id
        FROM registrations
        WHERE tournament_id = ?
        AND telegram_id = ?
        """,
        (
            tournament_id,
            user_id
        )
    ).fetchone()

    if exists:

        await callback.answer(
            "Ты уже подал заявку.",
            show_alert=True
        )

        return

    if tournament["max_players"]:

        count = db.execute(
            """
            SELECT COUNT(*) AS count
            FROM registrations
            WHERE tournament_id = ?
            AND status != 'rejected'
            """,
            (tournament_id,)
        ).fetchone()["count"]

        if count >= tournament["max_players"]:

            await callback.answer(
                "Турнир уже заполнен.",
                show_alert=True
            )

            return

    db.execute(
        """
        INSERT INTO registrations
        (
            tournament_id,
            telegram_id,
            status,
            created_at
        )
        VALUES (?, ?, 'pending', ?)
        """,
        (
            tournament_id,
            user_id,
            datetime.utcnow().isoformat()
        )
    )

    db.commit()

    await callback.message.edit_text(
        "✅ ЗАЯВКА ОТПРАВЛЕНА!\n\n"
        f"🏆 {tournament['name']}\n"
        f"🎮 Формат: {tournament['mode']}\n"
        "📌 Статус: ⏳ Ожидает подтверждения."
    )

    await callback.answer()


# ============================================================
# MY APPLICATIONS
# ============================================================

@dp.callback_query(lambda c: c.data == "my_applications")
async def applications_handler(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    rows = db.execute(
        """
        SELECT
            tournaments.name,
            tournaments.mode,
            registrations.status
        FROM registrations
        JOIN tournaments
        ON tournaments.id = registrations.tournament_id
        WHERE registrations.telegram_id = ?
        ORDER BY registrations.id DESC
        """,
        (callback.from_user.id,)
    ).fetchall()

    if not rows:

        text = T(
            lang,
            "no_applications"
        )

    else:

        text = "📋 МОИ ЗАЯВКИ\n\n"

        for row in rows:

            text += (
                f"🏆 {row['name']}\n"
                f"🎮 {row['mode']}\n"
                f"📌 {row['status']}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard(
            lang,
            "tournaments"
        )
    )

    await callback.answer()


# ============================================================
# RANKING
# ============================================================

@dp.callback_query(lambda c: c.data == "ranking")
async def ranking_handler(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        "📊 RANKING\n\n"
        "Выбери рейтинг:",
        reply_markup=ranking_keyboard(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "player_ranking")
async def player_ranking(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    rows = db.execute(
        """
        SELECT
            nickname,
            rating,
            wins,
            losses
        FROM users
        WHERE nickname != ''
        ORDER BY rating DESC, wins DESC
        LIMIT 20
        """
    ).fetchall()

    if not rows:

        text = T(
            lang,
            "ranking_empty"
        )

    else:

        text = "🥇 PLAYER RANKING\n\n"

        for index, row in enumerate(
            rows,
            1
        ):

            medal = {
                1: "🥇",
                2: "🥈",
                3: "🥉"
            }.get(
                index,
                f"{index}."
            )

            text += (
                f"{medal} {row['nickname']}"
                f" — ⭐ {row['rating']}\n"
                f"   🏆 {row['wins']} / "
                f"❌ {row['losses']}\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard(
            lang,
            "ranking"
        )
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "team_ranking")
async def team_ranking(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    rows = db.execute(
        """
        SELECT
            name,
            rating,
            wins,
            losses
        FROM teams
        ORDER BY rating DESC, wins DESC
        LIMIT 20
        """
    ).fetchall()

    if not rows:

        text = T(
            lang,
            "ranking_empty"
        )

    else:

        text = "👥 TEAM RANKING\n\n"

        for index, row in enumerate(
            rows,
            1
        ):

            medal = {
                1: "🥇",
                2: "🥈",
                3: "🥉"
            }.get(
                index,
                f"{index}."
            )

            text += (
                f"{medal} {row['name']}"
                f" — ⭐ {row['rating']}\n"
                f"   🏆 {row['wins']} / "
                f"❌ {row['losses']}\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard(
            lang,
            "ranking"
        )
    )

    await callback.answer()


# ============================================================
# TEAMS
# ============================================================

@dp.callback_query(lambda c: c.data == "team")
async def team_handler(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        "👥 TEAM ARENA\n\n"
        "Создавай команду 3v3,\n"
        "приглашай игроков и\n"
        "поднимай рейтинг.",
        reply_markup=team_keyboard(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "create_team")
async def create_team(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    lang = get_language(user_id)

    if not is_registered(user_id):

        await callback.answer(
            T(lang, "not_registered"),
            show_alert=True
        )

        return

    exists = db.execute(
        """
        SELECT id
        FROM teams
        WHERE captain_id = ?
        """,
        (user_id,)
    ).fetchone()

    if exists:

        await callback.answer(
            "У тебя уже есть команда.",
            show_alert=True
        )

        return

    set_state(
        user_id,
        "team_name"
    )

    await callback.message.edit_text(
        "👥 Введи название команды:"
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "my_team")
async def my_team(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    lang = get_language(user_id)

    row = db.execute(
        """
        SELECT
            id,
            name,
            rating,
            wins,
            losses
        FROM teams
        WHERE captain_id = ?
        """,
        (user_id,)
    ).fetchone()

    if not row:

        await callback.message.edit_text(
            T(lang, "team_empty"),
            reply_markup=team_keyboard(lang)
        )

        await callback.answer()

        return

    members = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM team_members
        WHERE team_id = ?
        """,
        (row["id"],)
    ).fetchone()["count"]

    await callback.message.edit_text(
        f"👥 {row['name']}\n\n"
        f"⭐ Rating: {row['rating']}\n"
        f"🏆 Wins: {row['wins']}\n"
        f"❌ Losses: {row['losses']}\n"
        f"👤 Players: {members}/3",
        reply_markup=back_keyboard(
            lang,
            "team"
        )
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "team_invites")
async def team_invites(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        "🔗 TEAM INVITATIONS\n\n"
        "Система приглашений будет использоваться\n"
        "для набора игроков в команды.",
        reply_markup=back_keyboard(
            lang,
            "team"
        )
    )

    await callback.answer()


# ============================================================
# NEWS
# ============================================================

async def send_news(target, user_id):

    lang = get_language(user_id)

    rows = db.execute(
        """
        SELECT
            title,
            text
        FROM news
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()

    if not rows:

        text = T(
            lang,
            "no_news"
        )

    else:

        text = "📰 ARENA NEWS\n\n"

        for row in rows:

            text += (
                f"🔥 {row['title']}\n"
                f"{row['text']}\n\n"
            )

    keyboard = main_menu(lang)

    if isinstance(target, types.CallbackQuery):

        await target.message.edit_text(
            text,
            reply_markup=keyboard
        )

    else:

        await target.answer(
            text,
            reply_markup=keyboard
        )


@dp.callback_query(lambda c: c.data == "news")
async def news_handler(callback: types.CallbackQuery):

    await send_news(
        callback,
        callback.from_user.id
    )

    await callback.answer()


@dp.message(Command("news"))
async def news_command(message: types.Message):

    ensure_user(message.from_user)

    await send_news(
        message,
        message.from_user.id
    )


# ============================================================
# HELP
# ============================================================

@dp.callback_query(lambda c: c.data == "help")
async def help_handler(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        T(lang, "help_text"),
        reply_markup=back_keyboard(
            lang,
            "home"
        )
    )

    await callback.answer()


@dp.message(Command("help"))
async def help_command(message: types.Message):

    ensure_user(message.from_user)

    lang = get_language(message.from_user.id)

    await message.answer(
        T(lang, "help_text"),
        reply_markup=main_menu(lang)
    )


# ============================================================
# RULES
# ============================================================

@dp.callback_query(lambda c: c.data == "rules")
async def rules_handler(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        T(lang, "rules_text"),
        reply_markup=back_keyboard(
            lang,
            "home"
        )
    )

    await callback.answer()


# ============================================================
# TEXT INPUT
# ============================================================

@dp.message()
async def text_handler(message: types.Message):

    if not message.text:
        return

    ensure_user(message.from_user)

    user_id = message.from_user.id

    lang = get_language(user_id)

    text = message.text.strip()

    step, temp_nickname, temp_player_id = get_state(
        user_id
    )

    # --------------------------------------------------------
    # REGISTRATION — NICKNAME
    # --------------------------------------------------------

    if step == "nickname":

        if len(text) < 2 or len(text) > 30:

            await message.answer(
                "❌ Ник должен содержать "
                "от 2 до 30 символов."
            )

            return

        set_state(
            user_id,
            "player_id",
            nickname=text
        )

        await message.answer(
            T(lang, "ask_player_id")
        )

        return

    # --------------------------------------------------------
    # REGISTRATION — PLAYER ID
    # --------------------------------------------------------

    if step == "player_id":

        if len(text) < 2 or len(text) > 40:

            await message.answer(
                "❌ Проверь Player ID."
            )

            return

        set_state(
            user_id,
            "country",
            nickname=temp_nickname,
            player_id=text
        )

        await message.answer(
            T(lang, "ask_country")
        )

        return

    # --------------------------------------------------------
    # REGISTRATION — COUNTRY
    # --------------------------------------------------------

    if step == "country":

        if len(text) < 2 or len(text) > 40:

            await message.answer(
                "❌ Введи название страны."
            )

            return

        db.execute(
            """
            UPDATE users
            SET
                nickname = ?,
                player_id = ?,
                country = ?,
                rating = 1000,
                wins = 0,
                losses = 0,
                streak = 0,
                best_streak = 0,
                level = 1,
                xp = 0,
                reg_step = '',
                temp_nickname = '',
                temp_player_id = ''
            WHERE telegram_id = ?
            """,
            (
                temp_nickname,
                temp_player_id,
                text,
                user_id
            )
        )

        db.commit()

        await message.answer(
            T(lang, "registration_done"),
            reply_markup=main_menu(lang)
        )

        return

    # --------------------------------------------------------
    # TEAM NAME
    # --------------------------------------------------------

    if step == "team_name":

        if len(text) < 3 or len(text) > 30:

            await message.answer(
                "❌ Название команды должно "
                "быть от 3 до 30 символов."
            )

            return

        try:

            cursor = db.execute(
                """
                INSERT INTO teams
                (
                    name,
                    captain_id,
                    rating,
                    created_at
                )
                VALUES (?, ?, 1000, ?)
                """,
                (
                    text,
                    user_id,
                    datetime.utcnow().isoformat()
                )
            )

            team_id = cursor.lastrowid

            db.execute(
                """
                INSERT INTO team_members
                (
                    team_id,
                    telegram_id
                )
                VALUES (?, ?)
                """,
                (
                    team_id,
                    user_id
                )
            )

            db.commit()

            reset_state(user_id)

            await message.answer(
                f"👥 {text}\n\n"
                f"{T(lang, 'team_created')}",
                reply_markup=main_menu(lang)
            )

        except sqlite3.IntegrityError:

            await message.answer(
                "❌ Такое название команды уже занято."
            )

        return


# ============================================================
# ADMIN
# ============================================================

@dp.message(Command("admin"))
async def admin_command(message: types.Message):

    if not is_admin(message.from_user.id):

        lang = get_language(
            message.from_user.id
        )

        await message.answer(
            T(lang, "admin_only")
        )

        return

    await message.answer(
        "🛡️ BRAWL STARS ARENA — ADMIN\n\n"

        "/users — статистика\n"
        "/requests — заявки\n"
        "/newtournament — создать турнир\n"
        "/newnews — создать новость\n"
        "/close ID — закрыть турнир\n"
        "/approve ID — одобрить заявку\n"
        "/reject ID — отклонить заявку\n\n"

        "Создание турнира:\n"
        "/newtournament Название | 1v1 | Приз | Описание | Лимит\n\n"

        "Пример:\n"
        "/newtournament Night Cup | 1v1 | $50 | Weekly Arena | 32"
    )


@dp.message(Command("users"))
async def admin_users(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    users = db.execute(
        "SELECT COUNT(*) AS c FROM users"
    ).fetchone()["c"]

    registered = db.execute(
        """
        SELECT COUNT(*) AS c
        FROM users
        WHERE nickname != ''
        """
    ).fetchone()["c"]

    teams = db.execute(
        "SELECT COUNT(*) AS c FROM teams"
    ).fetchone()["c"]

    tournaments = db.execute(
        "SELECT COUNT(*) AS c FROM tournaments"
    ).fetchone()["c"]

    await message.answer(
        "📊 ARENA STATS\n\n"
        f"👤 Users: {users}\n"
        f"🎮 Registered: {registered}\n"
        f"👥 Teams: {teams}\n"
        f"🏆 Tournaments: {tournaments}"
    )


@dp.message(Command("requests"))
async def admin_requests(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    rows = db.execute(
        """
        SELECT
            registrations.id,
            users.nickname,
            tournaments.name,
            registrations.status
        FROM registrations
        JOIN users
        ON users.telegram_id = registrations.telegram_id
        JOIN tournaments
        ON tournaments.id = registrations.tournament_id
        ORDER BY registrations.id DESC
        LIMIT 50
        """
    ).fetchall()

    if not rows:

        await message.answer(
            "📋 Заявок пока нет."
        )

        return

    result = "📋 REQUESTS\n\n"

    for row in rows:

        result += (
            f"#{row['id']} "
            f"{row['nickname']}\n"
            f"🏆 {row['name']}\n"
            f"📌 {row['status']}\n\n"
        )

    await message.answer(
        result
    )


@dp.message(Command("newtournament"))
async def new_tournament(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    raw = message.text.partition(" ")[2].strip()

    parts = [
        x.strip()
        for x in raw.split("|")
    ]

    if len(parts) < 5:

        await message.answer(
            "❌ Формат:\n\n"
            "/newtournament "
            "Название | 1v1 | Приз | "
            "Описание | Лимит"
        )

        return

    name = parts[0]
    mode = parts[1].lower()
    prize = parts[2]
    description = parts[3]
    limit_raw = parts[4]

    if mode not in ("1v1", "3v3"):

        await message.answer(
            "❌ Формат должен быть 1v1 или 3v3."
        )

        return

    try:

        max_players = int(
            limit_raw
        )

        if max_players < 0:
            raise ValueError

    except ValueError:

        await message.answer(
            "❌ Лимит должен быть числом."
        )

        return

    db.execute(
        """
        INSERT INTO tournaments
        (
            name,
            mode,
            prize,
            description,
            status,
            max_players,
            created_at
        )
        VALUES (?, ?, ?, ?, 'open', ?, ?)
        """,
        (
            name,
            mode,
            prize,
            description,
            max_players,
            datetime.utcnow().isoformat()
        )
    )

    db.commit()

    await message.answer(
        "✅ ТУРНИР СОЗДАН!\n\n"
        f"🏆 {name}\n"
        f"🎮 {mode}\n"
        f"🎁 {prize}\n"
        f"👤 Лимит: "
        f"{max_players or '∞'}"
    )


@dp.message(Command("newnews"))
async def new_news(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    raw = message.text.partition(" ")[2].strip()

    parts = [
        x.strip()
        for x in raw.split("|", 1)
    ]

    if len(parts) != 2:

        await message.answer(
            "❌ Формат:\n"
            "/newnews Заголовок | Текст новости"
        )

        return

    title, text = parts

    db.execute(
        """
        INSERT INTO news
        (
            title,
            text,
            created_at
        )
        VALUES (?, ?, ?)
        """,
        (
            title,
            text,
            datetime.utcnow().isoformat()
        )
    )

    db.commit()

    await message.answer(
        "📰 Новость опубликована."
    )


@dp.message(Command("close"))
async def close_tournament(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    value = message.text.partition(" ")[2].strip()

    if not value.isdigit():

        await message.answer(
            "❌ Используй:\n"
            "/close ID"
        )

        return

    tournament_id = int(value)

    cursor = db.execute(
        """
        UPDATE tournaments
        SET status = 'closed'
        WHERE id = ?
        """,
        (tournament_id,)
    )

    db.commit()

    if cursor.rowcount == 0:

        await message.answer(
            "❌ Турнир не найден."
        )

    else:

        await message.answer(
            f"✅ Турнир #{tournament_id} закрыт."
        )


@dp.message(Command("approve"))
async def approve_request(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    value = message.text.partition(" ")[2].strip()

    if not value.isdigit():

        await message.answer(
            "❌ Используй:\n"
            "/approve ID"
        )

        return

    request_id = int(value)

    cursor = db.execute(
        """
        UPDATE registrations
        SET status = 'approved'
        WHERE id = ?
        """,
        (request_id,)
    )

    db.commit()

    if cursor.rowcount == 0:

        await message.answer(
            "❌ Заявка не найдена."
        )

    else:

        await message.answer(
            f"✅ Заявка #{request_id} одобрена."
        )


@dp.message(Command("reject"))
async def reject_request(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    value = message.text.partition(" ")[2].strip()

    if not value.isdigit():

        await message.answer(
            "❌ Используй:\n"
            "/reject ID"
        )

        return

    request_id = int(value)

    cursor = db.execute(
        """
        UPDATE registrations
        SET status = 'rejected'
        WHERE id = ?
        """,
        (request_id,)
    )

    db.commit()

    if cursor.rowcount == 0:

        await message.answer(
            "❌ Заявка не найдена."
        )

    else:

        await message.answer(
            f"❌ Заявка #{request_id} отклонена."
        )


# ============================================================
# START BOT
# ============================================================

async def main():

    print(
        "🔥 BRAWL STARS ARENA FINAL is running..."
    )

    await setup_commands()

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
