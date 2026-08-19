import os
import sqlite3
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ============================================================
# DATABASE
# ============================================================

db = sqlite3.connect("arena.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT DEFAULT '',
    language TEXT DEFAULT 'en',
    nickname TEXT DEFAULT '',
    player_id TEXT DEFAULT '',
    country TEXT DEFAULT '',
    rating INTEGER DEFAULT 1000,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    captain_id INTEGER NOT NULL,
    rating INTEGER DEFAULT 1000,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS team_members (
    team_id INTEGER,
    telegram_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mode TEXT NOT NULL,
    prize TEXT DEFAULT '',
    status TEXT DEFAULT 'open'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER,
    telegram_id INTEGER,
    team_id INTEGER DEFAULT NULL,
    status TEXT DEFAULT 'pending'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    text TEXT NOT NULL
)
""")

db.commit()


# ============================================================
# TEXTS
# ============================================================

TEXTS = {

    "ru": {
        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Добро пожаловать!\n\n"
            "Турниры • Команды • Рейтинги\n\n"
            "Здесь решают активность и мастерство.",

        "profile": "👤 Профиль",
        "tournaments": "🏆 Турниры",
        "team": "👥 Команда",
        "ranking": "📊 Рейтинг",
        "news": "📰 Новости",
        "settings": "⚙️ Настройки",
        "help": "❓ Помощь",
        "rules": "📜 Правила",

        "register": "📝 Регистрация",
        "stats": "📈 Статистика",

        "back": "⬅️ Назад",
        "home": "🏠 Главное меню",

        "choose_language":
            "🌐 Выберите язык:",

        "profile_title":
            "👤 ТВОЙ ПРОФИЛЬ\n\n",

        "not_registered":
            "Ты ещё не зарегистрирован.\n\n"
            "Нажми «📝 Регистрация», чтобы создать профиль.",

        "ask_nickname":
            "🎮 Введи свой ник в Brawl Stars:",

        "ask_player_id":
            "🆔 Теперь введи свой Player ID:",

        "ask_country":
            "🌎 Введи свою страну:",

        "registration_done":
            "✅ Регистрация завершена!\n\n"
            "Добро пожаловать в Brawl Stars Arena.\n"
            "Твой стартовый рейтинг: ⭐ 1000",

        "tournaments_empty":
            "🏆 Сейчас активных турниров нет.\n\n"
            "Следи за новостями — новые турниры появятся здесь.",

        "team_empty":
            "👥 У тебя пока нет команды.\n\n"
            "Для 3v3 команда должна состоять ровно из 3 игроков.",

        "ranking_text":
            "📊 RANKING\n\n"
            "⭐ PLAYER RANKING — индивидуальный рейтинг игроков.\n\n"
            "👥 TEAM RANKING — отдельный рейтинг команд 3v3.",

        "news_empty":
            "📰 Пока новостей нет.",

        "rules_text":
            "📜 ПРАВИЛА ARENA\n\n"
            "• Читы запрещены.\n"
            "• Сторонние программы запрещены.\n"
            "• Оскорбления и токсичное поведение запрещены.\n"
            "• Решение администрации является окончательным.\n"
            "• За нарушение правил игрок может быть дисквалифицирован.",

        "help_text":
            "❓ ПОМОЩЬ\n\n"
            "🏆 Турниры — участие в соревнованиях.\n"
            "👥 Команды — создание команды 3v3.\n"
            "📊 Рейтинг — рейтинг игроков и команд.\n"
            "👤 Профиль — твоя статистика.\n"
            "📰 Новости — актуальные объявления.\n\n"
            "Если нужна помощь администрации — обратись к администратору Arena.",

        "settings_text":
            "⚙️ НАСТРОЙКИ\n\n"
            "Здесь будут настройки языка, уведомлений и профиля.",

        "create_team":
            "➕ Создать команду",

        "my_team":
            "👥 Моя команда",

        "team_invites":
            "🔗 Приглашения",

        "player_ranking":
            "🥇 Игроки",

        "team_ranking":
            "👥 Команды"
    },


    "en": {
        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Welcome!\n\n"
            "Tournaments • Teams • Rankings\n\n"
            "Here, activity and skill matter.",

        "profile": "👤 Profile",
        "tournaments": "🏆 Tournaments",
        "team": "👥 Team",
        "ranking": "📊 Ranking",
        "news": "📰 News",
        "settings": "⚙️ Settings",
        "help": "❓ Help",
        "rules": "📜 Rules",

        "register": "📝 Registration",
        "stats": "📈 Statistics",

        "back": "⬅️ Back",
        "home": "🏠 Main Menu",

        "choose_language":
            "🌐 Choose your language:",

        "profile_title":
            "👤 YOUR PROFILE\n\n",

        "not_registered":
            "You are not registered yet.\n\n"
            "Press «📝 Registration» to create your profile.",

        "ask_nickname":
            "🎮 Enter your Brawl Stars nickname:",

        "ask_player_id":
            "🆔 Enter your Player ID:",

        "ask_country":
            "🌎 Enter your country:",

        "registration_done":
            "✅ Registration completed!\n\n"
            "Welcome to Brawl Stars Arena.\n"
            "Your starting rating: ⭐ 1000",

        "tournaments_empty":
            "🏆 There are no active tournaments right now.\n\n"
            "Follow the news for upcoming tournaments.",

        "team_empty":
            "👥 You don't have a team yet.\n\n"
            "A 3v3 team must have exactly 3 players.",

        "ranking_text":
            "📊 RANKING\n\n"
            "⭐ PLAYER RANKING — individual player rating.\n\n"
            "👥 TEAM RANKING — separate 3v3 team rating.",

        "news_empty":
            "📰 There are no news yet.",

        "rules_text":
            "📜 ARENA RULES\n\n"
            "• Cheats are forbidden.\n"
            "• Third-party programs are forbidden.\n"
            "• Insults and toxic behavior are forbidden.\n"
            "• Admin decisions are final.\n"
            "• Breaking the rules may result in disqualification.",

        "help_text":
            "❓ HELP\n\n"
            "🏆 Tournaments — compete in events.\n"
            "👥 Teams — create a 3v3 team.\n"
            "📊 Ranking — player and team rankings.\n"
            "👤 Profile — your statistics.\n"
            "📰 News — latest announcements.",

        "settings_text":
            "⚙️ SETTINGS\n\n"
            "Language, notifications and profile settings will be available here.",

        "create_team":
            "➕ Create Team",

        "my_team":
            "👥 My Team",

        "team_invites":
            "🔗 Invitations",

        "player_ranking":
            "🥇 Players",

        "team_ranking":
            "👥 Teams"
    },


    "uz": {
        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Xush kelibsiz!\n\n"
            "Turnirlar • Jamoalar • Reytinglar\n\n"
            "Bu yerda mahorat va faollik muhim.",

        "profile": "👤 Profil",
        "tournaments": "🏆 Turnirlar",
        "team": "👥 Jamoa",
        "ranking": "📊 Reyting",
        "news": "📰 Yangiliklar",
        "settings": "⚙️ Sozlamalar",
        "help": "❓ Yordam",
        "rules": "📜 Qoidalar",

        "register": "📝 Ro'yxatdan o'tish",
        "stats": "📈 Statistika",

        "back": "⬅️ Orqaga",
        "home": "🏠 Bosh menyu",

        "choose_language":
            "🌐 Tilni tanlang:",

        "profile_title":
            "👤 PROFILINGIZ\n\n",

        "not_registered":
            "Siz hali ro'yxatdan o'tmagansiz.\n\n"
            "Profil yaratish uchun «📝 Ro'yxatdan o'tish» tugmasini bosing.",

        "ask_nickname":
            "🎮 Brawl Stars nikkingizni kiriting:",

        "ask_player_id":
            "🆔 Player ID ni kiriting:",

        "ask_country":
            "🌎 Davlatingizni kiriting:",

        "registration_done":
            "✅ Ro'yxatdan o'tish yakunlandi!\n\n"
            "Brawl Stars Arena'ga xush kelibsiz.\n"
            "Boshlang'ich reyting: ⭐ 1000",

        "tournaments_empty":
            "🏆 Hozircha faol turnirlar yo'q.",

        "team_empty":
            "👥 Sizda hali jamoa yo'q.\n\n"
            "3v3 jamoa aynan 3 o'yinchidan iborat bo'lishi kerak.",

        "ranking_text":
            "📊 REYTING\n\n"
            "⭐ O'YINCHILAR REYTINGI\n"
            "Har bir o'yinchining alohida reytingi.\n\n"
            "👥 JAMOALAR REYTINGI\n"
            "3v3 jamoalar uchun alohida reyting.",

        "news_empty":
            "📰 Hozircha yangiliklar yo'q.",

        "rules_text":
            "📜 ARENA QOIDALARI\n\n"
            "• Cheat taqiqlangan.\n"
            "• Begona dasturlar taqiqlangan.\n"
            "• Haqorat va toksik xatti-harakatlar taqiqlangan.",

        "help_text":
            "❓ YORDAM\n\n"
            "🏆 Turnirlar — musobaqalarda qatnashing.\n"
            "👥 Jamoalar — 3v3 jamoa yarating.\n"
            "📊 Reyting — o'yinchi va jamoalar reytingi.\n"
            "👤 Profil — statistika.\n"
            "📰 Yangiliklar — so'nggi xabarlar.",

        "settings_text":
            "⚙️ SOZLAMALAR\n\n"
            "Til, bildirishnomalar va profil sozlamalari.",

        "create_team":
            "➕ Jamoa yaratish",

        "my_team":
            "👥 Mening jamoam",

        "team_invites":
            "🔗 Takliflar",

        "player_ranking":
            "🥇 O'yinchilar",

        "team_ranking":
            "👥 Jamoalar"
    },


    "pt": {
        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Bem-vindo!\n\n"
            "Torneios • Equipes • Rankings\n\n"
            "Aqui, atividade e habilidade importam.",

        "profile": "👤 Perfil",
        "tournaments": "🏆 Torneios",
        "team": "👥 Equipe",
        "ranking": "📊 Ranking",
        "news": "📰 Notícias",
        "settings": "⚙️ Configurações",
        "help": "❓ Ajuda",
        "rules": "📜 Regras",

        "register": "📝 Registro",
        "stats": "📈 Estatísticas",

        "back": "⬅️ Voltar",
        "home": "🏠 Menu Principal",

        "choose_language":
            "🌐 Escolha seu idioma:",

        "profile_title":
            "👤 SEU PERFIL\n\n",

        "not_registered":
            "Você ainda não está registrado.\n\n"
            "Pressione «📝 Registro» para criar seu perfil.",

        "ask_nickname":
            "🎮 Digite seu apelido no Brawl Stars:",

        "ask_player_id":
            "🆔 Digite seu Player ID:",

        "ask_country":
            "🌎 Digite seu país:",

        "registration_done":
            "✅ Registro concluído!\n\n"
            "Bem-vindo à Brawl Stars Arena.\n"
            "Seu rating inicial: ⭐ 1000",

        "tournaments_empty":
            "🏆 Não há torneios ativos no momento.",

        "team_empty":
            "👥 Você ainda não possui uma equipe.\n\n"
            "Uma equipe 3v3 deve ter exatamente 3 jogadores.",

        "ranking_text":
            "📊 RANKING\n\n"
            "⭐ RANKING DE JOGADORES\n"
            "Cada jogador terá um ranking individual.\n\n"
            "👥 RANKING DE EQUIPES\n"
            "As equipes terão um ranking separado.",

        "news_empty":
            "📰 Ainda não há notícias.",

        "rules_text":
            "📜 REGRAS DA ARENA\n\n"
            "• Cheats são proibidos.\n"
            "• Programas de terceiros são proibidos.\n"
            "• Ofensas e comportamento tóxico são proibidos.",

        "help_text":
            "❓ AJUDA\n\n"
            "🏆 Torneios — participe das competições.\n"
            "👥 Equipes — crie uma equipe 3v3.\n"
            "📊 Ranking — jogadores e equipes.\n"
            "👤 Perfil — suas estatísticas.\n"
            "📰 Notícias — últimos anúncios.",

        "settings_text":
            "⚙️ CONFIGURAÇÕES\n\n"
            "Idioma, notificações e configurações do perfil.",

        "create_team":
            "➕ Criar equipe",

        "my_team":
            "👥 Minha equipe",

        "team_invites":
            "🔗 Convites",

        "player_ranking":
            "🥇 Jogadores",

        "team_ranking":
            "👥 Equipes"
    }
}


# ============================================================
# USER
# ============================================================

def create_user(user):
    cursor.execute(
        "SELECT telegram_id FROM users WHERE telegram_id = ?",
        (user.id,)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO users
            (telegram_id, username)
            VALUES (?, ?)
            """,
            (user.id, user.username or "")
        )
        db.commit()


def get_language(user_id):
    cursor.execute(
        "SELECT language FROM users WHERE telegram_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    return result[0] if result else "en"


def set_language(user_id, language):
    cursor.execute(
        """
        UPDATE users
        SET language = ?
        WHERE telegram_id = ?
        """,
        (language, user_id)
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

    t = TEXTS[lang]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t["tournaments"],
                    callback_data="tournaments"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["profile"],
                    callback_data="profile"
                ),
                InlineKeyboardButton(
                    text=t["ranking"],
                    callback_data="ranking"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["team"],
                    callback_data="team"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["news"],
                    callback_data="news"
                ),
                InlineKeyboardButton(
                    text=t["settings"],
                    callback_data="settings"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["help"],
                    callback_data="help"
                ),
                InlineKeyboardButton(
                    text=t["rules"],
                    callback_data="rules"
                )
            ]
        ]
    )


def profile_menu(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t["register"],
                    callback_data="register"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["stats"],
                    callback_data="stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["back"],
                    callback_data="home"
                )
            ]
        ]
    )


def team_menu(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t["create_team"],
                    callback_data="create_team"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["my_team"],
                    callback_data="my_team"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["team_invites"],
                    callback_data="team_invites"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["back"],
                    callback_data="home"
                )
            ]
        ]
    )


def ranking_menu(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t["player_ranking"],
                    callback_data="player_ranking"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["team_ranking"],
                    callback_data="team_ranking"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["back"],
                    callback_data="home"
                )
            ]
        ]
    )


def back_menu(lang):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=TEXTS[lang]["back"],
                    callback_data="home"
                )
            ]
        ]
    )


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def start(message: types.Message):

    create_user(message.from_user)

    await message.answer(
        "🏆 BRAWL STARS ARENA\n\n"
        "🇷🇺 Добро пожаловать в Brawl Stars Arena!\n"
        "Турниры • Команды • Рейтинги\n"
        "Здесь решают активность и мастерство.\n\n"
        "🇬🇧 Welcome to Brawl Stars Arena!\n"
        "Tournaments • Teams • Rankings\n"
        "Here, activity and skill matter.\n\n"
        "🌎 Выберите язык / Choose your language:",
        reply_markup=language_keyboard()
    )


# ============================================================
# LANGUAGE
# ============================================================

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def language_selected(callback: types.CallbackQuery):

    lang = callback.data.replace("lang_", "")

    create_user(callback.from_user)
    set_language(callback.from_user.id, lang)

    await callback.message.edit_text(
        TEXTS[lang]["welcome"],
        reply_markup=main_menu(lang)
    )

    await callback.answer()


# ============================================================
# HOME
# ============================================================

@dp.callback_query(lambda c: c.data == "home")
async def home(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["welcome"],
        reply_markup=main_menu(lang)
    )

    await callback.answer()


# ============================================================
# PROFILE
# ============================================================

@dp.callback_query(lambda c: c.data == "profile")
async def profile(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        """
        SELECT nickname, player_id, country,
               rating, wins, losses
        FROM users
        WHERE telegram_id = ?
        """,
        (callback.from_user.id,)
    )

    user = cursor.fetchone()

    if not user:
        text = TEXTS[lang]["not_registered"]

    else:

        nickname, player_id, country, rating, wins, losses = user

        if not nickname:
            text = TEXTS[lang]["not_registered"]
        else:
            text = (
                f"{TEXTS[lang]['profile_title']}"
                f"🎮 Nickname: {nickname}\n"
                f"🆔 Player ID: {player_id}\n"
                f"🌎 Country: {country}\n\n"
                f"⭐ Rating: {rating}\n"
                f"🏆 Wins: {wins}\n"
                f"❌ Losses: {losses}"
            )

    await callback.message.edit_text(
        text,
        reply_markup=profile_menu(lang)
    )

    await callback.answer()


# ============================================================
# REGISTRATION
# ============================================================

registration_state = {}


@dp.callback_query(lambda c: c.data == "register")
async def register_start(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    registration_state[callback.from_user.id] = {
        "step": "nickname"
    }

    await callback.message.edit_text(
        TEXTS[lang]["ask_nickname"]
    )

    await callback.answer()


@dp.message()
async def registration_messages(message: types.Message):

    user_id = message.from_user.id

    if user_id not in registration_state:
        return

    state = registration_state[user_id]
    lang = get_language(user_id)

    if state["step"] == "nickname":

        state["nickname"] = message.text
        state["step"] = "player_id"

        await message.answer(
            TEXTS[lang]["ask_player_id"]
        )

        return

    if state["step"] == "player_id":

        state["player_id"] = message.text
        state["step"] = "country"

        await message.answer(
            TEXTS[lang]["ask_country"]
        )

        return

    if state["step"] == "country":

        country = message.text

        nickname = state["nickname"]
        player_id = state["player_id"]

        cursor.execute(
            """
            UPDATE users
            SET nickname = ?,
                player_id = ?,
                country = ?
            WHERE telegram_id = ?
            """,
            (
                nickname,
                player_id,
                country,
                user_id
            )
        )

        db.commit()

        del registration_state[user_id]

        await message.answer(
            TEXTS[lang]["registration_done"],
            reply_markup=main_menu(lang)
        )


# ============================================================
# STATISTICS
# ============================================================

@dp.callback_query(lambda c: c.data == "stats")
async def stats(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        """
        SELECT nickname, rating, wins, losses
        FROM users
        WHERE telegram_id = ?
        """,
        (callback.from_user.id,)
    )

    user = cursor.fetchone()

    if not user or not user[0]:

        text = TEXTS[lang]["not_registered"]

    else:

        nickname, rating, wins, losses = user

        total = wins + losses

        text = (
            f"📈 STATISTICS\n\n"
            f"🎮 {nickname}\n\n"
            f"⭐ Rating: {rating}\n"
            f"🏆 Wins: {wins}\n"
            f"❌ Losses: {losses}\n"
            f"🎯 Matches: {total}"
        )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(lang)
    )

    await callback.answer()


# ============================================================
# TOURNAMENTS
# ============================================================

@dp.callback_query(lambda c: c.data == "tournaments")
async def tournaments(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        """
        SELECT name, mode, prize
        FROM tournaments
        WHERE status = 'open'
        """
    )

    items = cursor.fetchall()

    if not items:

        text = TEXTS[lang]["tournaments_empty"]

    else:

        text = "🏆 TOURNAMENTS\n\n"

        for name, mode, prize in items:

            text += (
                f"🔥 {name}\n"
                f"🎮 {mode}\n"
                f"🎁 {prize}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(lang)
    )

    await callback.answer()


# ============================================================
# TEAM
# ============================================================

@dp.callback_query(lambda c: c.data == "team")
async def team(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["team_empty"],
        reply_markup=team_menu(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "create_team")
async def create_team(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        "👥 CREATE TEAM\n\n"
        "Эта функция будет добавлена следующим этапом.\n\n"
        "Команда будет состоять ровно из 3 игроков.",
        reply_markup=back_menu(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "my_team")
async def my_team(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["team_empty"],
        reply_markup=back_menu(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "team_invites")
async def team_invites(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        "🔗 INVITATIONS\n\n"
        "Система приглашений будет добавлена следующим этапом.",
        reply_markup=back_menu(lang)
    )

    await callback.answer()


# ============================================================
# RANKING
# ============================================================

@dp.callback_query(lambda c: c.data == "ranking")
async def ranking(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["ranking_text"],
        reply_markup=ranking_menu(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "player_ranking")
async def player_ranking(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        """
        SELECT nickname, rating
        FROM users
        WHERE nickname != ''
        ORDER BY rating DESC
        LIMIT 10
        """
    )

    players = cursor.fetchall()

    if not players:

        text = "🥇 PLAYER RANKING\n\nNo registered players yet."

    else:

        text = "🥇 PLAYER RANKING\n\n"

        for index, (nickname, rating) in enumerate(players, 1):

            text += (
                f"{index}. {nickname} — ⭐ {rating}\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "team_ranking")
async def team_ranking(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        """
        SELECT name, rating
        FROM teams
        ORDER BY rating DESC
        LIMIT 10
        """
    )

    teams = cursor.fetchall()

    if not teams:

        text = "👥 TEAM RANKING\n\nNo teams yet."

    else:

        text = "👥 TEAM RANKING\n\n"

        for index, (name, rating) in enumerate(teams, 1):

            text += (
                f"{index}. {name} — ⭐ {rating}\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(lang)
    )

    await callback.answer()


# ============================================================
# NEWS
# ============================================================

@dp.callback_query(lambda c: c.data == "news")
async def news(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        """
        SELECT title, text
        FROM news
        ORDER BY id DESC
        LIMIT 10
        """
    )

    items = cursor.fetchall()

    if not items:

        text = TEXTS[lang]["news_empty"]

    else:

        text = "📰 NEWS\n\n"

        for title, news_text in items:

            text += (
                f"🔥 {title}\n"
                f"{news_text}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(lang)
    )

    await callback.answer()


# ============================================================
# SETTINGS
# ============================================================

@dp.callback_query(lambda c: c.data == "settings")
async def settings(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["settings_text"],
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=TEXTS[lang]["language"],
                        callback_data="language"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=TEXTS[lang]["back"],
                        callback_data="home"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# ============================================================
# LANGUAGE SETTINGS
# ============================================================

@dp.callback_query(lambda c: c.data == "language")
async def language_settings(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "🌐 Выберите язык / Choose your language:",
        reply_markup=language_keyboard()
    )

    await callback.answer()


# ============================================================
# HELP
# ============================================================

@dp.callback_query(lambda c: c.data == "help")
async def help_menu(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["help_text"],
        reply_markup=back_menu(lang)
    )

    await callback.answer()


# ============================================================
# RULES
# ============================================================

@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["rules_text"],
        reply_markup=back_menu(lang)
    )

    await callback.answer()


# ============================================================
# RUN
# ============================================================

async def main():

    print("🔥 BRAWL STARS ARENA is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
