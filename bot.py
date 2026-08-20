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
# BRAWL STARS ARENA
# ADMIN PANEL + REGISTRATION CONTROL
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

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT DEFAULT ''
);
""")

db.commit()


# ============================================================
# SETTINGS
# ============================================================

def init_settings():

    defaults = {
        "registration_enabled": "1",
        "tournament_registration_enabled": "1",
    }

    for key, value in defaults.items():

        db.execute(
            """
            INSERT OR IGNORE INTO settings(key, value)
            VALUES (?, ?)
            """,
            (key, value)
        )

    db.commit()


init_settings()


def get_setting(key, default="0"):

    row = db.execute(
        """
        SELECT value
        FROM settings
        WHERE key = ?
        """,
        (key,)
    ).fetchone()

    if not row:
        return default

    return row["value"]


def set_setting(key, value):

    db.execute(
        """
        INSERT INTO settings(key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        (key, str(value))
    )

    db.commit()


def registration_enabled():

    return get_setting(
        "registration_enabled",
        "1"
    ) == "1"


def tournament_registration_enabled():

    return get_setting(
        "tournament_registration_enabled",
        "1"
    ) == "1"


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

        "not_registered":
            "👤 Профиль ещё не создан.\n\n"
            "Нажми «📝 Регистрация».",

        "already_registered":
            "Ты уже зарегистрирован.",

        "registration_closed":
            "🔴 РЕГИСТРАЦИЯ ЗАКРЫТА\n\n"
            "Администрация временно закрыла регистрацию.\n"
            "Следи за новостями Arena.",

        "tournament_registration_closed":
            "🔴 ПОДАЧА ЗАЯВОК ЗАКРЫТА\n\n"
            "Администрация временно закрыла регистрацию "
            "на турниры.",

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

        "admin_only":
            "🛡️ Эта функция доступна только администрации.",

        "team_empty":
            "👥 У тебя пока нет команды.\n\n"
            "Создай команду для участия в 3v3.",

        "team_created":
            "👥 Команда создана!\n\n"
            "Теперь пригласи ещё двух игроков.",

        "ranking_empty":
            "📊 Пока недостаточно данных для рейтинга.",

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
            "🔥 Играем честно. Побеждает сильнейший."
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

        "not_registered":
            "👤 Your profile is not created yet.\n\n"
            "Press «📝 Registration».",

        "already_registered":
            "You are already registered.",

        "registration_closed":
            "🔴 REGISTRATION CLOSED\n\n"
            "Registration is temporarily closed.",

        "tournament_registration_closed":
            "🔴 TOURNAMENT REGISTRATION CLOSED\n\n"
            "Tournament applications are temporarily closed.",

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

        "admin_only":
            "🛡️ This feature is for administrators only.",

        "team_empty":
            "👥 You don't have a team yet.",

        "team_created":
            "👥 Team created!",

        "ranking_empty":
            "📊 Not enough data for the ranking yet.",

        "settings_text":
            "⚙️ SETTINGS\n\nChoose your interface language.",

        "help_text":
            "❓ HELP\n\n"
            "🏆 Tournaments — join competitions.\n"
            "👤 Profile — your profile and stats.\n"
            "📊 Ranking — players and teams.\n"
            "👥 Team — create a 3v3 team.\n"
            "📰 News — Arena events.",

        "rules_text":
            "📜 BRAWL STARS ARENA RULES\n\n"
            "1. Cheats are forbidden.\n"
            "2. Fake results are forbidden.\n"
            "3. Toxic behavior is forbidden.\n"
            "4. Match fixing is forbidden.\n"
            "5. Admin decisions are final."
    },

    "uz": {

        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Arenaga xush kelibsiz!\n\n"
            "⚔️ Turnirlar • 👥 Jamoalar • 📊 Reyting",

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

        "not_registered":
            "👤 Profilingiz hali yaratilmagan.",

        "already_registered":
            "Siz allaqachon ro‘yxatdan o‘tgansiz.",

        "registration_closed":
            "🔴 RO‘YXATDAN O‘TISH YOPIQ\n\n"
            "Ro‘yxatdan o‘tish vaqtincha yopilgan.",

        "tournament_registration_closed":
            "🔴 TURNIR RO‘YXATI YOPIQ\n\n"
            "Turnirlarga ariza topshirish vaqtincha yopilgan.",

        "ask_nickname":
            "🎮 Brawl Stars nikkingizni kiriting:",

        "ask_player_id":
            "🆔 Player ID ni kiriting:",

        "ask_country":
            "🌎 Davlatingizni kiriting:",

        "registration_done":
            "🔥 RO‘YXATDAN O‘TISH YAKUNLANDI!\n\n"
            "⭐ Boshlang‘ich reyting: 1000\n"
            "🎯 Daraja: 1\n"
            "💎 XP: 0",

        "no_tournaments":
            "🏆 Hozircha ochiq turnirlar yo‘q.",

        "no_news":
            "📰 Hozircha yangiliklar yo‘q.",

        "no_applications":
            "📋 Sizda hali arizalar yo‘q.",

        "admin_only":
            "🛡️ Bu funksiya faqat administratorlar uchun.",

        "team_empty":
            "👥 Sizda hali jamoa yo‘q.",

        "team_created":
            "👥 Jamoa yaratildi!",

        "ranking_empty":
            "📊 Reyting uchun ma’lumot yetarli emas.",

        "settings_text":
            "⚙️ SOZLAMALAR\n\nInterfeys tilini tanlang.",

        "help_text":
            "❓ YORDAM\n\n"
            "🏆 Turnirlar — musobaqalarda qatnashing.\n"
            "👤 Profil — profil va statistika.\n"
            "📊 Reyting — o‘yinchilar va jamoalar.\n"
            "👥 Jamoa — 3v3 jamoa yarating.",

        "rules_text":
            "📜 ARENA QOIDALARI\n\n"
            "1. Cheat taqiqlangan.\n"
            "2. Soxta natijalar taqiqlangan.\n"
            "3. Toksik xatti-harakat taqiqlangan.\n"
            "4. Kelishilgan natijalar taqiqlangan.\n"
            "5. Admin qarori yakuniy."
    },

    "pt": {

        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Bem-vindo à arena!\n\n"
            "⚔️ Torneios • 👥 Equipes • 📊 Rankings",

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

        "not_registered":
            "👤 Seu perfil ainda não foi criado.",

        "already_registered":
            "Você já está registrado.",

        "registration_closed":
            "🔴 REGISTRO FECHADO\n\n"
            "O registro está temporariamente fechado.",

        "tournament_registration_closed":
            "🔴 INSCRIÇÕES FECHADAS\n\n"
            "As inscrições para torneios estão temporariamente fechadas.",

        "ask_nickname":
            "🎮 Digite seu apelido no Brawl Stars:",

        "ask_player_id":
            "🆔 Digite seu Player ID:",

        "ask_country":
            "🌎 Digite seu país:",

        "registration_done":
            "🔥 REGISTRO CONCLUÍDO!\n\n"
            "⭐ Rating inicial: 1000\n"
            "🎯 Nível: 1\n"
            "💎 XP: 0",

        "no_tournaments":
            "🏆 Não há torneios abertos no momento.",

        "no_news":
            "📰 Ainda não há notícias.",

        "no_applications":
            "📋 Você ainda não possui inscrições.",

        "admin_only":
            "🛡️ Esta função é apenas para administradores.",

        "team_empty":
            "👥 Você ainda não possui uma equipe.",

        "team_created":
            "👥 Equipe criada!",

        "ranking_empty":
            "📊 Ainda não há dados suficientes.",

        "settings_text":
            "⚙️ CONFIGURAÇÕES\n\nEscolha o idioma.",

        "help_text":
            "❓ AJUDA\n\n"
            "🏆 Torneios — participe das competições.\n"
            "👤 Perfil — seu perfil e estatísticas.\n"
            "📊 Ranking — jogadores e equipes.\n"
            "👥 Equipe — crie uma equipe 3v3.",

        "rules_text":
            "📜 REGRAS DA ARENA\n\n"
            "1. Cheats são proibidos.\n"
            "2. Resultados falsos são proibidos.\n"
            "3. Comportamento tóxico é proibido.\n"
            "4. Resultados combinados são proibidos.\n"
            "5. A decisão do admin é final."
    }
}


# ============================================================
# TRANSLATION
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

    return row["language"] if row["language"] in TEXTS else "ru"


def set_language(user_id, lang):

    if lang not in TEXTS:
        lang = "ru"

    db.execute(
        """
        UPDATE users
        SET language = ?
        WHERE telegram_id = ?
        """,
        (lang, user_id)
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
# MAIN MENU
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
                    text="🏆 ТУРНИРЫ",
                    callback_data="tournaments"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="profile"
                ),
                InlineKeyboardButton(
                    text="📊 Рейтинг",
                    callback_data="ranking"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 Команда",
                    callback_data="team"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📰 Новости",
                    callback_data="news"
                ),
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="settings"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❓ Помощь",
                    callback_data="help"
                ),
                InlineKeyboardButton(
                    text="📜 Правила",
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
# ADMIN PANEL
# ============================================================

def admin_keyboard():

    reg = "🟢 ВКЛ" if registration_enabled() else "🔴 ВЫКЛ"
    tour_reg = (
        "🟢 ВКЛ"
        if tournament_registration_enabled()
        else
        "🔴 ВЫКЛ"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users"
                ),
                InlineKeyboardButton(
                    text="📋 Заявки",
                    callback_data="admin_requests"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏆 Турниры",
                    callback_data="admin_tournaments"
                ),
                InlineKeyboardButton(
                    text="➕ Создать турнир",
                    callback_data="admin_create_tournament"
                )
            ],

            [
                InlineKeyboardButton(
                    text=f"📝 Регистрация: {reg}",
                    callback_data="admin_toggle_registration"
                )
            ],

            [
                InlineKeyboardButton(
                    text=f"🏆 Заявки на турниры: {tour_reg}",
                    callback_data="admin_toggle_tournament_registration"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📰 Новости",
                    callback_data="admin_news"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 Рассылка",
                    callback_data="admin_broadcast"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="home"
                )
            ]
        ]
    )


async def show_admin_panel(message, edit=False):

    text = (
        "🛡️ BRAWL STARS ARENA\n"
        "👑 ADMIN PANEL\n\n"
        "Управление проектом находится здесь.\n\n"
        f"📝 Регистрация: "
        f"{'🟢 ВКЛ' if registration_enabled() else '🔴 ВЫКЛ'}\n"
        f"🏆 Заявки на турниры: "
        f"{'🟢 ВКЛ' if tournament_registration_enabled() else '🔴 ВЫКЛ'}"
    )

    if edit:
        await message.edit_text(
            text,
            reply_markup=admin_keyboard()
        )
    else:
        await message.answer(
            text,
            reply_markup=admin_keyboard()
        )


# ============================================================
# COMMANDS
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
        ),
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

    lang = get_language(callback.from_user.id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=T(lang, "language"),
                    callback_data="language"
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

    await callback.message.edit_text(
        T(lang, "settings_text"),
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

        text = T(lang, "not_registered")

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

    if not registration_enabled():

        await callback.answer(
            T(lang, "registration_closed"),
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

        text = T(lang, "not_registered")

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


async def show_tournaments(callback, mode):

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

        count = db.execute(
            """
            SELECT COUNT(*) AS c
            FROM registrations
            WHERE tournament_id = ?
            AND status != 'rejected'
            """,
            (row["id"],)
        ).fetchone()["c"]

        text += (
            f"🔥 {row['name']}\n"
            f"🎁 Приз: {row['prize'] or '—'}\n"
            f"👤 Игроков: {count}/"
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

    await show_tournaments(callback, "1v1")


@dp.callback_query(lambda c: c.data == "tour_3v3")
async def tournament_3v3(callback: types.CallbackQuery):

    await show_tournaments(callback, "3v3")


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

        text = T(lang, "no_tournaments")

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

    if not tournament_registration_enabled():

        await callback.answer(
            T(lang, "tournament_registration_closed"),
            show_alert=True
        )

        return

    if not is_registered(user_id):

        await callback.answer(
            T(lang, "not_registered"),
            show_alert=True
        )

        return

    tournament_id = int(callback.data[5:])

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
            "❌ Турнир не найден.",
            show_alert=True
        )

        return

    if tournament["status"] != "open":

        await callback.answer(
            "🔴 Турнир закрыт.",
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
            "⚠️ Ты уже подал заявку.",
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
                "❌ Турнир уже заполнен.",
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

        text = T(lang, "no_applications")

    else:

        text = "📋 МОИ ЗАЯВКИ\n\n"

        status_names = {
            "pending": "⏳ Ожидание",
            "approved": "✅ Одобрено",
            "rejected": "❌ Отклонено"
        }

        for row in rows:

            text += (
                f"🏆 {row['name']}\n"
                f"🎮 {row['mode']}\n"
                f"📌 {status_names.get(row['status'], row['status'])}\n\n"
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
        "📊 RANKING\n\nВыбери рейтинг:",
        reply_markup=ranking_keyboard(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "player_ranking")
async def player_ranking(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    rows = db.execute(
        """
        SELECT nickname, rating, wins, losses
        FROM users
        WHERE nickname != ''
        ORDER BY rating DESC, wins DESC
        LIMIT 20
        """
    ).fetchall()

    if not rows:

        text = T(lang, "ranking_empty")

    else:

        text = "🥇 PLAYER RANKING\n\n"

        for index, row in enumerate(rows, 1):

            medal = {
                1: "🥇",
                2: "🥈",
                3: "🥉"
            }.get(index, f"{index}.")

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
        SELECT name, rating, wins, losses
        FROM teams
        ORDER BY rating DESC, wins DESC
        LIMIT 20
        """
    ).fetchall()

    if not rows:

        text = T(lang, "ranking_empty")

    else:

        text = "👥 TEAM RANKING\n\n"

        for index, row in enumerate(rows, 1):

            medal = {
                1: "🥇",
                2: "🥈",
                3: "🥉"
            }.get(index, f"{index}.")

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
            "⚠️ У тебя уже есть команда.",
            show_alert=True
        )

        return

    set_state(user_id, "team_name")

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
        SELECT title, text
        FROM news
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()

    if not rows:

        text = T(lang, "no_news")

    else:

        text = "📰 ARENA NEWS\n\n"

        for row in rows:

            text += (
                f"🔥 {row['title']}\n"
                f"{row['text']}\n\n"
            )

    if isinstance(target, types.CallbackQuery):

        await target.message.edit_text(
            text,
            reply_markup=main_menu(lang)
        )

    else:

        await target.answer(
            text,
            reply_markup=main_menu(lang)
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

    step, temp_nickname, temp_player_id = get_state(user_id)

    # --------------------------------------------------------
    # NICKNAME
    # --------------------------------------------------------

    if step == "nickname":

        if not registration_enabled():

            reset_state(user_id)

            await message.answer(
                T(lang, "registration_closed")
            )

            return

        if len(text) < 2 or len(text) > 30:

            await message.answer(
                "❌ Ник должен содержать от 2 до 30 символов."
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
    # PLAYER ID
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
    # COUNTRY
    # --------------------------------------------------------

    if step == "country":

        if len(text) < 2 or len(text) > 40:

            await message.answer(
                "❌ Введи название страны."
            )

            return

        if not registration_enabled():

            reset_state(user_id)

            await message.answer(
                T(lang, "registration_closed")
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
                "❌ Название команды должно быть от 3 до 30 символов."
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
# ADMIN COMMAND
# ============================================================

@dp.message(Command("admin"))
async def admin_command(message: types.Message):

    ensure_user(message.from_user)

    if not is_admin(message.from_user.id):

        await message.answer(
            T(
                get_language(message.from_user.id),
                "admin_only"
            )
        )

        return

    await show_admin_panel(message)


# ============================================================
# ADMIN CALLBACK SECURITY
# ============================================================

async def admin_check(callback):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "🛡️ Только для администрации.",
            show_alert=True
        )

        return False

    return True


# ============================================================
# ADMIN — MAIN
# ============================================================

@dp.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel_callback(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    await show_admin_panel(
        callback.message,
        edit=True
    )

    await callback.answer()


# ============================================================
# ADMIN — STATISTICS
# ============================================================

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):

    if not await admin_check(callback):
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

    open_tournaments = db.execute(
        """
        SELECT COUNT(*) AS c
        FROM tournaments
        WHERE status = 'open'
        """
    ).fetchone()["c"]

    applications = db.execute(
        """
        SELECT COUNT(*) AS c
        FROM registrations
        """
    ).fetchone()["c"]

    pending = db.execute(
        """
        SELECT COUNT(*) AS c
        FROM registrations
        WHERE status = 'pending'
        """
    ).fetchone()["c"]

    text = (
        "📊 ARENA STATISTICS\n\n"
        f"👤 Пользователей: {users}\n"
        f"🎮 Зарегистрировано: {registered}\n"
        f"👥 Команд: {teams}\n\n"
        f"🏆 Турниров: {tournaments}\n"
        f"🔥 Открыто: {open_tournaments}\n\n"
        f"📋 Заявок: {applications}\n"
        f"⏳ Ожидают: {pending}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить",
                        callback_data="admin_stats"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Админ-панель",
                        callback_data="admin_panel"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# ============================================================
# ADMIN — USERS
# ============================================================

@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users_callback(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    rows = db.execute(
        """
        SELECT
            telegram_id,
            username,
            nickname,
            rating
        FROM users
        ORDER BY telegram_id DESC
        LIMIT 20
        """
    ).fetchall()

    text = "👥 ПОСЛЕДНИЕ ПОЛЬЗОВАТЕЛИ\n\n"

    if not rows:

        text += "Пользователей пока нет."

    else:

        for row in rows:

            nickname = row["nickname"] or "Без профиля"
            username = (
                f"@{row['username']}"
                if row["username"]
                else "без username"
            )

            text += (
                f"👤 {nickname}\n"
                f"🔗 {username}\n"
                f"⭐ {row['rating']}\n"
                f"🆔 {row['telegram_id']}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Админ-панель",
                        callback_data="admin_panel"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# ============================================================
# ADMIN — TOGGLE REGISTRATION
# ============================================================

@dp.callback_query(lambda c: c.data == "admin_toggle_registration")
async def admin_toggle_registration(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    current = registration_enabled()

    set_setting(
        "registration_enabled",
        "0" if current else "1"
    )

    status = "🟢 включена" if not current else "🔴 выключена"

    await callback.answer(
        f"Регистрация {status}",
        show_alert=True
    )

    await show_admin_panel(
        callback.message,
        edit=True
    )


# ============================================================
# ADMIN — TOGGLE TOURNAMENT REGISTRATION
# ============================================================

@dp.callback_query(
    lambda c:
        c.data == "admin_toggle_tournament_registration"
)
async def admin_toggle_tournament_registration(
    callback: types.CallbackQuery
):

    if not await admin_check(callback):
        return

    current = tournament_registration_enabled()

    set_setting(
        "tournament_registration_enabled",
        "0" if current else "1"
    )

    status = (
        "🟢 включена"
        if not current
        else
        "🔴 выключена"
    )

    await callback.answer(
        f"Подача заявок {status}",
        show_alert=True
    )

    await show_admin_panel(
        callback.message,
        edit=True
    )


# ============================================================
# ADMIN — REQUESTS
# ============================================================

def admin_requests_keyboard():

    rows = db.execute(
        """
        SELECT
            registrations.id,
            users.nickname,
            tournaments.name,
            registrations.status
        FROM registrations
        JOIN users
        ON users.telegram_id =
            registrations.telegram_id
        JOIN tournaments
        ON tournaments.id =
            registrations.tournament_id
        WHERE registrations.status = 'pending'
        ORDER BY registrations.id ASC
        LIMIT 20
        """
    ).fetchall()

    buttons = []

    for row in rows:

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"⏳ #{row['id']} {row['nickname']}",
                    callback_data=f"admin_req_{row['id']}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Админ-панель",
                callback_data="admin_panel"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


@dp.callback_query(lambda c: c.data == "admin_requests")
async def admin_requests_callback(callback: types.CallbackQuery):

    if not await admin_check(callback):
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
        ON users.telegram_id =
            registrations.telegram_id
        JOIN tournaments
        ON tournaments.id =
            registrations.tournament_id
        WHERE registrations.status = 'pending'
        ORDER BY registrations.id ASC
        LIMIT 20
        """
    ).fetchall()

    if not rows:

        text = (
            "📋 ЗАЯВКИ\n\n"
            "✅ Нет заявок, ожидающих проверки."
        )

    else:

        text = (
            "📋 ЗАЯВКИ\n\n"
            f"⏳ Ожидают проверки: {len(rows)}\n\n"
            "Выбери заявку:"
        )

    await callback.message.edit_text(
        text,
        reply_markup=admin_requests_keyboard()
    )

    await callback.answer()


# ============================================================
# ADMIN — REQUEST DETAILS
# ============================================================

@dp.callback_query(
    lambda c:
        c.data.startswith("admin_req_")
        and c.data[10:].isdigit()
)
async def admin_request_details(
    callback: types.CallbackQuery
):

    if not await admin_check(callback):
        return

    request_id = int(
        callback.data[10:]
    )

    row = db.execute(
        """
        SELECT
            registrations.id,
            registrations.telegram_id,
            registrations.status,
            registrations.created_at,

            users.nickname,
            users.player_id,
            users.country,
            users.rating,
            users.wins,
            users.losses,

            tournaments.name,
            tournaments.mode,
            tournaments.prize

        FROM registrations

        JOIN users
        ON users.telegram_id =
            registrations.telegram_id

        JOIN tournaments
        ON tournaments.id =
            registrations.tournament_id

        WHERE registrations.id = ?
        """,
        (request_id,)
    ).fetchone()

    if not row:

        await callback.answer(
            "❌ Заявка не найдена.",
            show_alert=True
        )

        return

    status = {
        "pending": "⏳ Ожидает",
        "approved": "✅ Одобрена",
        "rejected": "❌ Отклонена"
    }.get(
        row["status"],
        row["status"]
    )

    text = (
        "📋 ЗАЯВКА\n\n"
        f"🆔 Заявка: #{row['id']}\n"
        f"📌 Статус: {status}\n\n"

        f"👤 Ник: {row['nickname']}\n"
        f"🆔 Player ID: {row['player_id']}\n"
        f"🌎 Страна: {row['country']}\n"
        f"⭐ Рейтинг: {row['rating']}\n"
        f"🏆 Победы: {row['wins']}\n"
        f"❌ Поражения: {row['losses']}\n\n"

        f"🏆 Турнир: {row['name']}\n"
        f"🎮 Формат: {row['mode']}\n"
        f"🎁 Приз: {row['prize'] or '—'}"
    )

    buttons = []

    if row["status"] == "pending":

        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"admin_approve_{row['id']}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"admin_reject_{row['id']}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ К заявкам",
                callback_data="admin_requests"
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


# ============================================================
# ADMIN — APPROVE
# ============================================================

@dp.callback_query(
    lambda c:
        c.data.startswith("admin_approve_")
        and c.data[14:].isdigit()
)
async def admin_approve(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    request_id = int(
        callback.data[14:]
    )

    row = db.execute(
        """
        SELECT
            telegram_id,
            tournament_id
        FROM registrations
        WHERE id = ?
        """,
        (request_id,)
    ).fetchone()

    if not row:

        await callback.answer(
            "❌ Заявка не найдена.",
            show_alert=True
        )

        return

    cursor = db.execute(
        """
        UPDATE registrations
        SET status = 'approved'
        WHERE id = ?
        AND status = 'pending'
        """,
        (request_id,)
    )

    db.commit()

    if cursor.rowcount == 0:

        await callback.answer(
            "⚠️ Заявка уже обработана.",
            show_alert=True
        )

        return

    await callback.answer(
        "✅ Заявка одобрена!",
        show_alert=True
    )

    # Уведомляем игрока
    try:

        tournament = db.execute(
            """
            SELECT name, mode
            FROM tournaments
            WHERE id = ?
            """,
            (row["tournament_id"],)
        ).fetchone()

        await bot.send_message(
            row["telegram_id"],
            "🎉 ЗАЯВКА ОДОБРЕНА!\n\n"
            f"🏆 {tournament['name']}\n"
            f"🎮 Формат: {tournament['mode']}\n\n"
            "🔥 Удачи на арене!"
        )

    except Exception as e:

        print(
            f"Notification error: {e}"
        )

    await callback.message.edit_text(
        "✅ Заявка одобрена!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ К заявкам",
                        callback_data="admin_requests"
                    )
                ]
            ]
        )
    )


# ============================================================
# ADMIN — REJECT
# ============================================================

@dp.callback_query(
    lambda c:
        c.data.startswith("admin_reject_")
        and c.data[13:].isdigit()
)
async def admin_reject(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    request_id = int(
        callback.data[13:]
    )

    row = db.execute(
        """
        SELECT
            telegram_id,
            tournament_id
        FROM registrations
        WHERE id = ?
        """,
        (request_id,)
    ).fetchone()

    if not row:

        await callback.answer(
            "❌ Заявка не найдена.",
            show_alert=True
        )

        return

    cursor = db.execute(
        """
        UPDATE registrations
        SET status = 'rejected'
        WHERE id = ?
        AND status = 'pending'
        """,
        (request_id,)
    )

    db.commit()

    if cursor.rowcount == 0:

        await callback.answer(
            "⚠️ Заявка уже обработана.",
            show_alert=True
        )

        return

    await callback.answer(
        "❌ Заявка отклонена.",
        show_alert=True
    )

    try:

        tournament = db.execute(
            """
            SELECT name
            FROM tournaments
            WHERE id = ?
            """,
            (row["tournament_id"],)
        ).fetchone()

        await bot.send_message(
            row["telegram_id"],
            "❌ ЗАЯВКА ОТКЛОНЕНА\n\n"
            f"🏆 {tournament['name']}\n\n"
            "Если ты считаешь это ошибкой — "
            "обратись к администрации."
        )

    except Exception as e:

        print(
            f"Notification error: {e}"
        )

    await callback.message.edit_text(
        "❌ Заявка отклонена.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ К заявкам",
                        callback_data="admin_requests"
                    )
                ]
            ]
        )
    )


# ============================================================
# ADMIN — TOURNAMENTS
# ============================================================

@dp.callback_query(lambda c: c.data == "admin_tournaments")
async def admin_tournaments(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    rows = db.execute(
        """
        SELECT
            id,
            name,
            mode,
            prize,
            status,
            max_players
        FROM tournaments
        ORDER BY id DESC
        LIMIT 30
        """
    ).fetchall()

    text = "🏆 УПРАВЛЕНИЕ ТУРНИРАМИ\n\n"

    buttons = []

    if not rows:

        text += "Турниров пока нет."

    else:

        for row in rows:

            status = (
                "🟢 ОТКРЫТ"
                if row["status"] == "open"
                else
                "🔴 ЗАКРЫТ"
            )

            text += (
                f"#{row['id']} — {row['name']}\n"
                f"🎮 {row['mode']} | "
                f"{status}\n"
                f"🎁 {row['prize'] or '—'}\n\n"
            )

            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"⚙️ #{row['id']} {row['name']}",
                        callback_data=f"admin_tour_{row['id']}"
                    )
                ]
            )

    buttons.append(
        [
            InlineKeyboardButton(
                text="➕ Создать турнир",
                callback_data="admin_create_tournament"
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Админ-панель",
                callback_data="admin_panel"
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


# ============================================================
# ADMIN — TOURNAMENT DETAILS
# ============================================================

@dp.callback_query(
    lambda c:
        c.data.startswith("admin_tour_")
        and c.data[11:].isdigit()
)
async def admin_tournament_details(
    callback: types.CallbackQuery
):

    if not await admin_check(callback):
        return

    tournament_id = int(
        callback.data[11:]
    )

    row = db.execute(
        """
        SELECT
            id,
            name,
            mode,
            prize,
            description,
            status,
            max_players
        FROM tournaments
        WHERE id = ?
        """,
        (tournament_id,)
    ).fetchone()

    if not row:

        await callback.answer(
            "❌ Турнир не найден.",
            show_alert=True
        )

        return

    count = db.execute(
        """
        SELECT COUNT(*) AS c
        FROM registrations
        WHERE tournament_id = ?
        AND status != 'rejected'
        """,
        (tournament_id,)
    ).fetchone()["c"]

    status = (
        "🟢 ОТКРЫТ"
        if row["status"] == "open"
        else
        "🔴 ЗАКРЫТ"
    )

    text = (
        "🏆 ТУРНИР\n\n"
        f"🆔 #{row['id']}\n"
        f"🏆 {row['name']}\n"
        f"🎮 Формат: {row['mode']}\n"
        f"🎁 Приз: {row['prize'] or '—'}\n"
        f"ℹ️ {row['description'] or '—'}\n\n"
        f"👥 Участников: {count}/"
        f"{row['max_players'] or '∞'}\n"
        f"📌 Статус: {status}"
    )

    buttons = []

    if row["status"] == "open":

        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔴 Закрыть турнир",
                    callback_data=f"admin_close_tour_{row['id']}"
                )
            ]
        )

    else:

        buttons.append(
            [
                InlineKeyboardButton(
                    text="🟢 Открыть турнир",
                    callback_data=f"admin_open_tour_{row['id']}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="📋 Заявки",
                callback_data=f"admin_tour_requests_{row['id']}"
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Турниры",
                callback_data="admin_tournaments"
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


# ============================================================
# ADMIN — CLOSE TOURNAMENT
# ============================================================

@dp.callback_query(
    lambda c:
        c.data.startswith("admin_close_tour_")
        and c.data[17:].isdigit()
)
async def admin_close_tournament(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    tournament_id = int(
        callback.data[17:]
    )

    db.execute(
        """
        UPDATE tournaments
        SET status = 'closed'
        WHERE id = ?
        """,
        (tournament_id,)
    )

    db.commit()

    await callback.answer(
        "🔴 Турнир закрыт.",
        show_alert=True
    )

    callback.data = f"admin_tour_{tournament_id}"

    await admin_tournament_details(callback)


# ============================================================
# ADMIN — OPEN TOURNAMENT
# ============================================================

@dp.callback_query(
    lambda c:
        c.data.startswith("admin_open_tour_")
        and c.data[16:].isdigit()
)
async def admin_open_tournament(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    tournament_id = int(
        callback.data[16:]
    )

    db.execute(
        """
        UPDATE tournaments
        SET status = 'open'
        WHERE id = ?
        """,
        (tournament_id,)
    )

    db.commit()

    await callback.answer(
        "🟢 Турнир открыт.",
        show_alert=True
    )

    callback.data = f"admin_tour_{tournament_id}"

    await admin_tournament_details(callback)


# ============================================================
# ADMIN — TOURNAMENT REQUESTS
# ============================================================

@dp.callback_query(
    lambda c:
        c.data.startswith("admin_tour_requests_")
        and c.data[21:].isdigit()
)
async def admin_tournament_requests(
    callback: types.CallbackQuery
):

    if not await admin_check(callback):
        return

    tournament_id = int(
        callback.data[21:]
    )

    rows = db.execute(
        """
        SELECT
            registrations.id,
            users.nickname,
            users.rating,
            registrations.status
        FROM registrations
        JOIN users
        ON users.telegram_id =
            registrations.telegram_id
        WHERE registrations.tournament_id = ?
        ORDER BY registrations.id ASC
        """,
        (tournament_id,)
    ).fetchall()

    if not rows:

        text = "📋 Участников пока нет."

    else:

        text = "📋 ЗАЯВКИ ТУРНИРА\n\n"

        for row in rows:

            status = {
                "pending": "⏳",
                "approved": "✅",
                "rejected": "❌"
            }.get(
                row["status"],
                "❔"
            )

            text += (
                f"{status} #{row['id']} "
                f"{row['nickname']}\n"
                f"⭐ {row['rating']}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Турнир",
                        callback_data=f"admin_tour_{tournament_id}"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# ============================================================
# ADMIN — CREATE TOURNAMENT
# ============================================================

@dp.callback_query(
    lambda c:
        c.data == "admin_create_tournament"
)
async def admin_create_tournament(
    callback: types.CallbackQuery
):

    if not await admin_check(callback):
        return

    set_state(
        callback.from_user.id,
        "admin_new_tournament"
    )

    await callback.message.edit_text(
        "➕ СОЗДАНИЕ ТУРНИРА\n\n"
        "Отправь одной строкой:\n\n"
        "Название | 1v1 | Приз | Описание | Лимит\n\n"
        "Пример:\n"
        "Night Cup | 1v1 | $50 | Weekly Arena | 32\n\n"
        "Для безлимитного турнира укажи 0."
    )

    await callback.answer()


# ============================================================
# ADMIN — NEWS MENU
# ============================================================

@dp.callback_query(lambda c: c.data == "admin_news")
async def admin_news(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    rows = db.execute(
        """
        SELECT id, title
        FROM news
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()

    text = "📰 УПРАВЛЕНИЕ НОВОСТЯМИ\n\n"

    if not rows:

        text += "Новостей пока нет."

    else:

        for row in rows:
            text += (
                f"#{row['id']} — "
                f"{row['title']}\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Создать новость",
                        callback_data="admin_create_news"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Админ-панель",
                        callback_data="admin_panel"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# ============================================================
# ADMIN — CREATE NEWS
# ============================================================

@dp.callback_query(lambda c: c.data == "admin_create_news")
async def admin_create_news(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    set_state(
        callback.from_user.id,
        "admin_new_news"
    )

    await callback.message.edit_text(
        "📰 СОЗДАНИЕ НОВОСТИ\n\n"
        "Отправь:\n\n"
        "Заголовок | Текст новости\n\n"
        "Пример:\n"
        "Night Cup #1 | Регистрация открыта!"
    )

    await callback.answer()


# ============================================================
# ADMIN — BROADCAST
# ============================================================

@dp.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast(callback: types.CallbackQuery):

    if not await admin_check(callback):
        return

    set_state(
        callback.from_user.id,
        "admin_broadcast"
    )

    await callback.message.edit_text(
        "📢 РАССЫЛКА\n\n"
        "Отправь сообщение, которое нужно "
        "разослать всем пользователям.\n\n"
        "⚠️ Используй эту функцию аккуратно."
    )

    await callback.answer()


# ============================================================
# ADMIN TEXT INPUT
# ============================================================

async def handle_admin_text(message):

    if not is_admin(message.from_user.id):
        return False

    user_id = message.from_user.id

    step, temp_nickname, temp_player_id = get_state(
        user_id
    )

    text = message.text.strip()

    # --------------------------------------------------------
    # CREATE TOURNAMENT
    # --------------------------------------------------------

    if step == "admin_new_tournament":

        parts = [
            x.strip()
            for x in text.split("|")
        ]

        if len(parts) < 5:

            await message.answer(
                "❌ Неверный формат.\n\n"
                "Название | 1v1 | Приз | Описание | Лимит"
            )

            return True

        name = parts[0]
        mode = parts[1].lower()
        prize = parts[2]
        description = parts[3]

        try:

            max_players = int(parts[4])

            if max_players < 0:
                raise ValueError

        except ValueError:

            await message.answer(
                "❌ Лимит должен быть числом."
            )

            return True

        if mode not in ("1v1", "3v3"):

            await message.answer(
                "❌ Формат должен быть 1v1 или 3v3."
            )

            return True

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

        reset_state(user_id)

        await message.answer(
            "✅ ТУРНИР СОЗДАН!\n\n"
            f"🏆 {name}\n"
            f"🎮 {mode}\n"
            f"🎁 {prize}\n"
            f"👤 Лимит: "
            f"{max_players or '∞'}",
            reply_markup=admin_keyboard()
        )

        return True

    # --------------------------------------------------------
    # CREATE NEWS
    # --------------------------------------------------------

    if step == "admin_new_news":

        parts = [
            x.strip()
            for x in text.split("|", 1)
        ]

        if len(parts) != 2:

            await message.answer(
                "❌ Формат:\n"
                "Заголовок | Текст новости"
            )

            return True

        title, news_text = parts

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
                news_text,
                datetime.utcnow().isoformat()
            )
        )

        db.commit()

        reset_state(user_id)

        await message.answer(
            "📰 Новость опубликована!",
            reply_markup=admin_keyboard()
        )

        return True

    # --------------------------------------------------------
    # BROADCAST
    # --------------------------------------------------------

    if step == "admin_broadcast":

        reset_state(user_id)

        users = db.execute(
            """
            SELECT telegram_id
            FROM users
            """
        ).fetchall()

        sent = 0
        failed = 0

        await message.answer(
            "📢 Начинаю рассылку..."
        )

        for row in users:

            try:

                await bot.send_message(
                    row["telegram_id"],
                    "📢 BRAWL STARS ARENA\n\n"
                    + text
                )

                sent += 1

                await asyncio.sleep(0.05)

            except Exception:

                failed += 1

        await message.answer(
            "📢 РАССЫЛКА ЗАВЕРШЕНА\n\n"
            f"✅ Отправлено: {sent}\n"
            f"❌ Ошибок: {failed}",
            reply_markup=admin_keyboard()
        )

        return True

    return False


# ============================================================
# TEXT INPUT — ADMIN FIRST
# ============================================================

@dp.message()
async def final_text_handler(message: types.Message):

    if not message.text:
        return

    ensure_user(message.from_user)

    if is_admin(message.from_user.id):

        handled = await handle_admin_text(
            message
        )

        if handled:
            return

    user_id = message.from_user.id
    lang = get_language(user_id)
    text = message.text.strip()

    step, temp_nickname, temp_player_id = get_state(
        user_id
    )

    # --------------------------------------------------------
    # REGISTRATION NICKNAME
    # --------------------------------------------------------

    if step == "nickname":

        if not registration_enabled():

            reset_state(user_id)

            await message.answer(
                T(lang, "registration_closed")
            )

            return

        if len(text) < 2 or len(text) > 30:

            await message.answer(
                "❌ Ник должен содержать от 2 до 30 символов."
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
    # PLAYER ID
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
    # COUNTRY
    # --------------------------------------------------------

    if step == "country":

        if not registration_enabled():

            reset_state(user_id)

            await message.answer(
                T(lang, "registration_closed")
            )

            return

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
                "❌ Название команды должно быть от 3 до 30 символов."
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
# OLD COMMAND COMPATIBILITY
# ============================================================

@dp.message(Command("users"))
async def users_command(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📊 Используй /admin → 📊 Статистика"
    )


@dp.message(Command("requests"))
async def requests_command(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📋 Используй /admin → 📋 Заявки"
    )


@dp.message(Command("close"))
async def close_command(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    value = message.text.partition(" ")[2].strip()

    if not value.isdigit():

        await message.answer(
            "❌ Используй /close ID"
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

    if cursor.rowcount:

        await message.answer(
            f"🔴 Турнир #{tournament_id} закрыт."
        )

    else:

        await message.answer(
            "❌ Турнир не найден."
        )


# ============================================================
# START BOT
# ============================================================

async def main():

    print(
        "🔥 BRAWL STARS ARENA — ADMIN EDITION is running..."
    )

    print(
        f"👑 Admin IDs: {ADMIN_IDS}"
    )

    print(
        f"📝 Registration: "
        f"{registration_enabled()}"
    )

    print(
        f"🏆 Tournament applications: "
        f"{tournament_registration_enabled()}"
    )

    await setup_commands()

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
