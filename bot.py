import os
import sqlite3
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.getenv("BOT_TOKEN")

# Сюда позже впишем твой Telegram ID для доступа к админке
ADMIN_IDS = {
    # 123456789,
}


if not TOKEN:
    raise ValueError("BOT_TOKEN is not set")


bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# DATABASE
# =========================

db = sqlite3.connect("arena.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
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
    description TEXT DEFAULT '',
    prize TEXT DEFAULT '',
    status TEXT DEFAULT 'open'
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


# =========================
# TEXTS
# =========================

TEXTS = {

    "ru": {
        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Добро пожаловать в Brawl Stars Arena!\n\n"
            "Турниры, команды, рейтинги и соревнования "
            "для игроков Brawl Stars.\n\n"
            "Здесь решают активность и мастерство.",

        "menu": "🏆 Главное меню",

        "profile": "👤 Профиль",
        "tournaments": "🏆 Турниры",
        "team": "👥 Команда",
        "rating": "📊 Рейтинг",
        "news": "📰 Новости",
        "rules": "📜 Правила",
        "language": "🌐 Язык",

        "profile_empty":
            "👤 Твой профиль\n\n"
            "Ник: не указан\n"
            "Player ID: не указан\n"
            "Страна: не указана\n\n"
            "⭐ Rating: 1000\n"
            "🏆 Победы: 0\n"
            "❌ Поражения: 0",

        "tournaments_empty":
            "🏆 Турниры\n\n"
            "Сейчас активных турниров нет.\n\n"
            "Когда появится новый турнир, "
            "он будет отображаться здесь.",

        "team_empty":
            "👥 Команды\n\n"
            "У тебя пока нет команды.\n\n"
            "Позже здесь можно будет создать команду "
            "из 3 игроков или присоединиться к существующей.",

        "rating_text":
            "📊 RANKINGS\n\n"
            "⭐ PLAYER RATING\n"
            "Система рейтинга работает отдельно для каждого игрока.\n\n"
            "👥 TEAM RATING\n"
            "У команд будет отдельный рейтинг.",

        "news_empty":
            "📰 Новости\n\n"
            "Пока новостей нет.",

        "rules_text":
            "📜 Правила Arena\n\n"
            "• Читы запрещены.\n"
            "• Запрещены оскорбления и токсичное поведение.\n"
            "• Нельзя использовать сторонние программы.\n"
            "• Решение администрации является окончательным.\n"
            "• За нарушение правил игрок может быть дисквалифицирован.",

        "choose_language":
            "🌐 Выберите язык / Choose your language:"
    },

    "en": {
        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Welcome to Brawl Stars Arena!\n\n"
            "Tournaments, teams, rankings and competition "
            "for Brawl Stars players.\n\n"
            "Here, activity and skill matter.",

        "menu": "🏆 Main Menu",

        "profile": "👤 Profile",
        "tournaments": "🏆 Tournaments",
        "team": "👥 Team",
        "rating": "📊 Rankings",
        "news": "📰 News",
        "rules": "📜 Rules",
        "language": "🌐 Language",

        "profile_empty":
            "👤 Your Profile\n\n"
            "Nickname: not set\n"
            "Player ID: not set\n"
            "Country: not set\n\n"
            "⭐ Rating: 1000\n"
            "🏆 Wins: 0\n"
            "❌ Losses: 0",

        "tournaments_empty":
            "🏆 Tournaments\n\n"
            "There are no active tournaments right now.\n\n"
            "New tournaments will appear here.",

        "team_empty":
            "👥 Teams\n\n"
            "You don't have a team yet.\n\n"
            "Later you will be able to create a 3-player "
            "team or join an existing one.",

        "rating_text":
            "📊 RANKINGS\n\n"
            "⭐ PLAYER RATING\n"
            "Each player will have an individual rating.\n\n"
            "👥 TEAM RATING\n"
            "Teams will have a separate rating.",

        "news_empty":
            "📰 News\n\n"
            "There are no news yet.",

        "rules_text":
            "📜 Arena Rules\n\n"
            "• Cheats are forbidden.\n"
            "• Toxic behavior and insults are forbidden.\n"
            "• Third-party programs are forbidden.\n"
            "• Admin decisions are final.\n"
            "• Breaking the rules may result in disqualification.",

        "choose_language":
            "🌐 Выберите язык / Choose your language:"
    },

    "uz": {
        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Brawl Stars Arena'ga xush kelibsiz!\n\n"
            "Turnirlar, jamoalar, reytinglar va musobaqalar.\n\n"
            "Bu yerda mahorat va faollik muhim.",

        "menu": "🏆 Asosiy menyu",

        "profile": "👤 Profil",
        "tournaments": "🏆 Turnirlar",
        "team": "👥 Jamoa",
        "rating": "📊 Reyting",
        "news": "📰 Yangiliklar",
        "rules": "📜 Qoidalar",
        "language": "🌐 Til",

        "profile_empty":
            "👤 Profilingiz\n\n"
            "Nik: kiritilmagan\n"
            "Player ID: kiritilmagan\n"
            "Davlat: kiritilmagan\n\n"
            "⭐ Reyting: 1000\n"
            "🏆 G'alabalar: 0\n"
            "❌ Mag'lubiyatlar: 0",

        "tournaments_empty":
            "🏆 Turnirlar\n\n"
            "Hozircha faol turnirlar yo'q.",

        "team_empty":
            "👥 Jamoalar\n\n"
            "Sizda hali jamoa yo'q.\n\n"
            "Keyinchalik 3 kishilik jamoa yaratishingiz "
            "yoki mavjud jamoaga qo'shilishingiz mumkin.",

        "rating_text":
            "📊 REYTING\n\n"
            "⭐ O'YINCHI REYTINGI\n"
            "Har bir o'yinchining alohida reytingi bo'ladi.\n\n"
            "👥 JAMOA REYTINGI\n"
            "Jamoalar uchun alohida reyting bo'ladi.",

        "news_empty":
            "📰 Yangiliklar\n\n"
            "Hozircha yangiliklar yo'q.",

        "rules_text":
            "📜 Arena qoidalari\n\n"
            "• Cheat taqiqlangan.\n"
            "• Haqorat va toksik xatti-harakatlar taqiqlangan.\n"
            "• Begona dasturlardan foydalanish taqiqlangan.\n"
            "• Administrator qarori yakuniy hisoblanadi.",

        "choose_language":
            "🌐 Tilni tanlang:"
    },

    "pt": {
        "welcome":
            "🏆 BRAWL STARS ARENA\n\n"
            "Bem-vindo à Brawl Stars Arena!\n\n"
            "Torneios, equipes, rankings e competições "
            "para jogadores de Brawl Stars.\n\n"
            "Aqui, atividade e habilidade importam.",

        "menu": "🏆 Menu Principal",

        "profile": "👤 Perfil",
        "tournaments": "🏆 Torneios",
        "team": "👥 Equipe",
        "rating": "📊 Ranking",
        "news": "📰 Notícias",
        "rules": "📜 Regras",
        "language": "🌐 Idioma",

        "profile_empty":
            "👤 Seu Perfil\n\n"
            "Apelido: não definido\n"
            "Player ID: não definido\n"
            "País: não definido\n\n"
            "⭐ Rating: 1000\n"
            "🏆 Vitórias: 0\n"
            "❌ Derrotas: 0",

        "tournaments_empty":
            "🏆 Torneios\n\n"
            "Não há torneios ativos no momento.",

        "team_empty":
            "👥 Equipes\n\n"
            "Você ainda não possui uma equipe.\n\n"
            "Mais tarde você poderá criar uma equipe "
            "de 3 jogadores ou entrar em uma existente.",

        "rating_text":
            "📊 RANKING\n\n"
            "⭐ RANKING DE JOGADORES\n"
            "Cada jogador terá um ranking individual.\n\n"
            "👥 RANKING DE EQUIPES\n"
            "As equipes terão um ranking separado.",

        "news_empty":
            "📰 Notícias\n\n"
            "Ainda não há notícias.",

        "rules_text":
            "📜 Regras da Arena\n\n"
            "• Cheats são proibidos.\n"
            "• Ofensas e comportamento tóxico são proibidos.\n"
            "• Programas de terceiros são proibidos.\n"
            "• As decisões dos administradores são finais.",

        "choose_language":
            "🌐 Escolha seu idioma:"
    }
}


# =========================
# DATABASE FUNCTIONS
# =========================

def create_user(user: types.User):
    cursor.execute(
        "SELECT telegram_id FROM users WHERE telegram_id = ?",
        (user.id,)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
            (user.id, user.username or "")
        )
        db.commit()


def get_language(user_id):
    cursor.execute(
        "SELECT language FROM users WHERE telegram_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return "en"


def set_language(user_id, language):
    cursor.execute(
        "UPDATE users SET language = ? WHERE telegram_id = ?",
        (language, user_id)
    )
    db.commit()


# =========================
# KEYBOARDS
# =========================

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
                    text=t["profile"],
                    callback_data="profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["tournaments"],
                    callback_data="tournaments"
                ),
                InlineKeyboardButton(
                    text=t["team"],
                    callback_data="team"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["rating"],
                    callback_data="rating"
                ),
                InlineKeyboardButton(
                    text=t["news"],
                    callback_data="news"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t["rules"],
                    callback_data="rules"
                ),
                InlineKeyboardButton(
                    text=t["language"],
                    callback_data="language"
                )
            ]
        ]
    )


def back_button(lang):
    text = {
        "ru": "⬅️ Назад",
        "en": "⬅️ Back",
        "uz": "⬅️ Orqaga",
        "pt": "⬅️ Voltar"
    }

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text[lang],
                    callback_data="back"
                )
            ]
        ]
    )


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: types.Message):

    create_user(message.from_user)

    lang = get_language(message.from_user.id)

    await message.answer(
        "🏆 BRAWL STARS ARENA\n\n"
        "🇷🇺 Добро пожаловать в Brawl Stars Arena!\n"
        "Турниры, команды, рейтинги и соревнования.\n"
        "Здесь решают активность и мастерство.\n\n"
        "🇬🇧 Welcome to Brawl Stars Arena!\n"
        "Tournaments, teams, rankings and competition.\n"
        "Here, activity and skill matter.\n\n"
        "🌎 Choose your language / Выберите язык:",
        reply_markup=language_keyboard()
    )


# =========================
# LANGUAGE
# =========================

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def language_selected(callback: types.CallbackQuery):

    lang = callback.data.replace("lang_", "")

    set_language(callback.from_user.id, lang)

    t = TEXTS[lang]

    await callback.message.edit_text(
        t["welcome"],
        reply_markup=main_menu(lang)
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "language")
async def language(callback: types.CallbackQuery):

    await callback.message.edit_text(
        TEXTS[get_language(callback.from_user.id)]["choose_language"],
        reply_markup=language_keyboard()
    )

    await callback.answer()


# =========================
# PROFILE
# =========================

@dp.callback_query(lambda c: c.data == "profile")
async def profile(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        """
        SELECT nickname, player_id, country, rating, wins, losses
        FROM users
        WHERE telegram_id = ?
        """,
        (callback.from_user.id,)
    )

    user = cursor.fetchone()

    if user:
        nickname, player_id, country, rating, wins, losses = user

        if not nickname:
            await callback.message.edit_text(
                TEXTS[lang]["profile_empty"],
                reply_markup=back_button(lang)
            )
        else:
            text = (
                f"👤 {TEXTS[lang]['profile']}\n\n"
                f"🎮 Nickname: {nickname}\n"
                f"🆔 Player ID: {player_id}\n"
                f"🌎 Country: {country}\n\n"
                f"⭐ Rating: {rating}\n"
                f"🏆 Wins: {wins}\n"
                f"❌ Losses: {losses}"
            )

            await callback.message.edit_text(
                text,
                reply_markup=back_button(lang)
            )

    await callback.answer()


# =========================
# TOURNAMENTS
# =========================

@dp.callback_query(lambda c: c.data == "tournaments")
async def tournaments(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        """
        SELECT name, mode, prize, status
        FROM tournaments
        WHERE status = 'open'
        """
    )

    tournaments_list = cursor.fetchall()

    if not tournaments_list:
        await callback.message.edit_text(
            TEXTS[lang]["tournaments_empty"],
            reply_markup=back_button(lang)
        )
    else:
        text = "🏆 TOURNAMENTS\n\n"

        for tournament in tournaments_list:
            name, mode, prize, status = tournament

            text += (
                f"🔥 {name}\n"
                f"🎮 Format: {mode}\n"
                f"🎁 Prize: {prize}\n\n"
            )

        await callback.message.edit_text(
            text,
            reply_markup=back_button(lang)
        )

    await callback.answer()


# =========================
# TEAM
# =========================

@dp.callback_query(lambda c: c.data == "team")
async def team(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["team_empty"],
        reply_markup=back_button(lang)
    )

    await callback.answer()


# =========================
# RATING
# =========================

@dp.callback_query(lambda c: c.data == "rating")
async def rating(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["rating_text"],
        reply_markup=back_button(lang)
    )

    await callback.answer()


# =========================
# NEWS
# =========================

@dp.callback_query(lambda c: c.data == "news")
async def news(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    cursor.execute(
        "SELECT title, text FROM news ORDER BY id DESC LIMIT 10"
    )

    news_list = cursor.fetchall()

    if not news_list:
        await callback.message.edit_text(
            TEXTS[lang]["news_empty"],
            reply_markup=back_button(lang)
        )

    else:
        text = "📰 NEWS\n\n"

        for title, news_text in news_list:
            text += f"🔥 {title}\n{news_text}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=back_button(lang)
        )

    await callback.answer()


# =========================
# RULES
# =========================

@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["rules_text"],
        reply_markup=back_button(lang)
    )

    await callback.answer()


# =========================
# BACK
# =========================

@dp.callback_query(lambda c: c.data == "back")
async def back(callback: types.CallbackQuery):

    lang = get_language(callback.from_user.id)

    await callback.message.edit_text(
        TEXTS[lang]["menu"],
        reply_markup=main_menu(lang)
    )

    await callback.answer()


# =========================
# RUN
# =========================

async def main():

    print("🔥 BRAWL STARS ARENA is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
