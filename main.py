"""
Telegram-бот «Перебей лидера» с системой доступа, настройками и языками RU/EN.

Роли:
    SUPERADMIN  — полный доступ
    ADMIN       — доступ к админ-панели
    APPROVED    — обычный юзер
    PENDING     — ожидает одобрения
    BANNED      — забанен
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Final, Optional

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


# ─────────────────────────── Конфигурация ───────────────────────────

BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "8980577514:AAEcyyyIIWrZlZZg2XoNyblIn9pQKsXgg3k")
BOT_USERNAME: Final[str] = os.getenv("BOT_USERNAME", "velem1Xbivbot")

SUPERADMIN_ID: Final[int] = 8093996396

DEFAULT_DURATION: Final[int] = 60
MIN_DURATION: Final[int] = 5
MAX_DURATION: Final[int] = 3600

BACKUP_FILE: Final[str] = "backup.json"

TIMER_UPDATE_EVERY: Final[int] = 5

log = logging.getLogger("biv-bot")


# ─────────────────────────── Переводы ───────────────────────────

STRINGS: Final[dict[str, dict[str, str]]] = {
    "ru": {
        "menu_title": "🛡 <b>Панель управления</b>",
        "menu_sub": "<i>выбери действие</i>",
        "btn_add_chat": "➕ Добавить в чат",
        "btn_profile": "👤 Профиль",
        "btn_my_chats": "📋 Мои чаты",
        "btn_admin_panel": "⚙️ Админ-панель",
        "btn_back": "⬅️ Назад",
        "bot_disabled": "🔧 Бот временно отключён.",
        "access_denied": "🚫 Доступ запрещён.",
        "request_new": "🔔 <b>Новая заявка на доступ</b>",
        "request_sent": (
            "⏳ <b>Доступ не выдан</b>\n\n"
            "Заявка отправлена администратору. Ожидай одобрения."
        ),
        "welcome": (
            "👋 Добро пожаловать.\n"
            "Добавь бота в чат и напиши /biv start 60."
        ),
        "profile_title": "👤 <b>Профиль</b>",
        "profile_id": "🆔 ID",
        "profile_name": "📛 Имя",
        "profile_username": "🔗 Юзернейм",
        "profile_role": "🎭 Роль",
        "profile_chats": "📋 Чатов с ботом",
        "role_superadmin": "👑 Супер-админ",
        "role_admin": "🛡 Админ",
        "role_banned": "🚫 Забанен",
        "role_user": "✅ Юзер",
        "role_pending": "⏳ Ожидает",
        "admin_panel_title": "⚙️ <b>Админ-панель</b>",
        "admin_panel_sub": "Выбери раздел 👇",
        "btn_users": "👥 Пользователи",
        "btn_stats": "📊 Статистика",
        "btn_settings": "⚙️ Настройки",
        "btn_backup": "💾 Бэкап",
        "users_title": "👥 <b>Пользователи</b>",
        "users_sub": "Выбери раздел 👇",
        "btn_all_users": "📜 Все юзеры",
        "btn_pending": "⏳ Ожидают одобрения",
        "btn_banned": "🚫 Забаненные",
        "btn_admins": "🛡 Админы",
        "pending_title": "⏳ <b>Ожидает одобрения</b>",
        "pending_empty": "⏳ <b>Ожидают одобрения:</b>\n\nникого нет",
        "banned_title": "🚫 <b>Забаненные:</b>",
        "banned_empty": "🚫 <b>Забаненные:</b>\n\nникого нет",
        "admins_title": "🛡 <b>Админы:</b>",
        "admins_super": "👑 Супер-админ",
        "admins_empty": "<i>обычных админов нет</i>",
        "all_users_title": "📜 <b>Все пользователи:</b>",
        "all_users_empty": "📜 <b>Все пользователи:</b>\n\nпока никого",
        "btn_approve": "✅ Одобрить",
        "btn_ban": "🚫 Забанить",
        "btn_unban": "♻️ Разбанить",
        "btn_makeadmin": "🛡 Сделать админом",
        "btn_removeadmin": "🗑 Снять админа",
        "btn_delete": "🗑 Удалить",
        "done": "Готово.",
        "no_access": "⛔ Нет доступа.",
        "only_superadmin": "⛔ Только супер-админ.",
        "cant_touch_super": "⛔ Супер-админа трогать нельзя.",
        "user_not_found": "Юзер не найден.",
        "id_error": "Ошибка ID.",
        "notify_approved": "✅ Доступ выдан.",
        "notify_banned": "🚫 Ты забанен.",
        "notify_unbanned": "♻️ Ты разбанен.",
        "notify_makeadmin": "🛡 Тебе выдали права админа.",
        "notify_removeadmin": "🗑 Права админа сняты.",
        "stats_title": "📊 <b>Статистика бота</b>",
        "stats_users": "👥 Всего юзеров",
        "stats_pending": "⏳ Ожидают",
        "stats_banned": "🚫 Забанено",
        "stats_admins": "🛡 Админов",
        "stats_chats": "📋 Чатов",
        "stats_wins": "🎮 Побед всего",
        "settings_title": "⚙️ <b>Настройки бота</b>",
        "settings_sub": "Меняй параметры ниже 👇",
        "btn_antiflood": "🚫 Антифлуд",
        "btn_badwords": "🚫 Чёрный список слов",
        "btn_lang": "🌐 Язык",
        "btn_notify": "🔔 Уведомления",
        "lang_title": "🌐 <b>Язык</b>",
        "lang_sub": "Выбери язык 👇",
        "lang_changed": "Язык изменён: {}",
        "notify_title": "🔔 <b>Уведомления</b>",
        "notify_sub": "Что присылать тебе в ЛС 👇",
        "notify_joins": "➕ Добавления в чат",
        "notify_leaves": "➖ Удаления из чата",
        "notify_requests": "🔔 Заявки на доступ",
        "notify_wins": "🏆 Победы в играх",
        "notify_updated": "Обновлено.",
        "words_title": "🚫 <b>Чёрный список слов</b>",
        "words_empty": "Список пуст.",
        "words_list": "🚫 Слова:",
        "words_added": "✅ Добавлено: <code>{}</code>",
        "words_deleted": "🗑 Удалено: <code>{}</code>",
        "words_exists": "Уже есть или пусто.",
        "words_not_found": "Такого слова нет.",
        "words_usage_add": "Использование: /addword слово",
        "words_usage_del": "Использование: /delword слово",
        "words_swear": "🚫 {}, не ругайся.",
        "backup_title": "💾 <b>Бэкап</b>",
        "backup_sub": "Экспорт сохраняет всех юзеров, статистику и чаты в файл на сервере.",
        "btn_export": "📤 Экспорт в файл",
        "btn_import": "📥 Импорт из файла",
        "btn_info": "ℹ️ О бэкапе",
        "backup_saved": "✅ <b>Бэкап сохранён</b>",
        "backup_restored": "✅ <b>Бэкап восстановлен</b>",
        "backup_error_export": "❌ Ошибка бэкапа:",
        "backup_error_import": "❌ Ошибка импорта:",
        "backup_no_file": "Файла нет.",
        "backup_info_title": "ℹ️ <b>О бэкапе</b>",
        "backup_file": "Файл",
        "backup_exists": "Существует",
        "backup_size": "Размер",
        "backup_bytes": "байт",
        "chats_title": "📋 <b>Чаты:</b>",
        "chats_empty": "📋 <b>Чаты:</b>\n\nпока пусто",
        "add_chat_title": "➕ <b>Как добавить бота в чат</b>",
        "add_chat_1": "<b>1.</b> Скопируй юзернейм:",
        "add_chat_2": "<b>2.</b> Чат → Управление → Добавить участника.",
        "add_chat_3": (
            "<b>3.</b> Управление → Администраторы → выдать права:\n"
            "     • Удаление сообщений\n"
            "     • Закрепление сообщений"
        ),
        "add_chat_4": "<b>4.</b> @BotFather → Group Privacy → Turn off",
        "add_chat_5": "<b>5.</b> В чате: <code>/biv start 60</code>",
        "chat_added_title": "✅ <b>Бот добавлен в чат</b>",
        "chat_removed_title": "❌ <b>Бот удалён из чата</b>",
        "chat_denied_title": "🚫 <b>Попытка добавить без доступа</b>",
        "chat_denied_msg": "⛔ Нет доступа. Бот покидает чат.",
        "chat_name": "📌 Название",
        "chat_id": "🆔 Chat ID",
        "chat_added_by": "👤 Добавил",
        "game_started": "🎮 Игра запущена",
        "game_seconds": "⏱ {} сек",
        "game_hint": "Пиши сообщение — станешь лидером.",
        "game_stopped": "🛑 Игра остановлена.",
        "game_already": "Игра уже идёт.",
        "game_not_running": "Игра и так не идёт.",
        "game_invalid_duration": "Время должно быть от {} до {} сек.",
        "game_bad_number": "Время должно быть числом. Пример: /biv start 60",
        "game_flood": "🔄 Перебито!",
        "game_new_leader": "Новый лидер",
        "game_time_left": "До конца",
        "game_winner": "🏆 Победитель",
        "game_message": "Сообщение",
        "top_title": "🏆 Топ игроков:",
        "top_empty": "📊 Пока нет ни одной победы в этом чате.",
        "top_players": "Всего игроков",
        "my_stats": "📈 Статистика {}",
        "my_stats_wins": "Побед",
        "my_stats_place": "Место",
        "my_stats_zero": "У {} пока 0 побед.",
        "reset_done": "🧹 Статистика сброшена.",
        "cmd_makeadmin_usage": "Использование: /makeadmin <user_id>",
        "cmd_unmakeadmin_usage": "Использование: /unmakeadmin <user_id>",
        "cmd_ban_usage": "Использование: /ban <user_id>",
        "cmd_unban_usage": "Использование: /unban <user_id>",
        "cmd_approve_usage": "Использование: /approve <user_id>",
        "cmd_id_number": "ID должен быть числом.",
        "cmd_made_admin": "✅ {} теперь админ.",
        "cmd_removed_admin": "🗑 {} больше не админ.",
        "cmd_banned": "🚫 {} забанен.",
        "cmd_unbanned": "♻️ {} разбанен.",
        "cmd_approved": "✅ {} одобрен.",
        "cmd_user_first_start": "Юзер не найден (пусть сначала напишет боту /start).",
        "user_card": (
            "👤 <b>Пользователь</b>\n\n"
            "📛 Имя: {name}\n"
            "🔗 Юзернейм: {username}\n"
            "🆔 ID: <code>{user_id}</code>\n"
            "🎭 Статус: {status}"
        ),
        "status_admin": "🛡 Админ",
        "status_banned": "🚫 Забанен",
        "status_user": "✅ Юзер",
        "status_pending": "⏳ Ожидает",
        "status_superadmin": "👑 Супер-админ",
        "quick_ban_title": "🚫 <b>Кого забанить?</b>\n\nВыбери пользователя:",
        "quick_ban_empty": "🚫 Некого банить — нет активных юзеров.",
        "quick_unban_title": "♻️ <b>Кого разбанить?</b>\n\nВыбери пользователя:",
        "quick_unban_empty": "♻️ Некого разбанить — нет забаненных.",
        "quick_add_admin_title": "🛡 <b>Кого сделать админом?</b>\n\nВыбери пользователя:",
        "quick_add_admin_empty": "🛡 Некого назначить — нет одобренных юзеров.",
        "quick_del_admin_title": "🗑 <b>С кого снять админа?</b>\n\nВыбери админа:",
        "quick_del_admin_empty": "🗑 Нет обычных админов.",
    },
    "en": {
        "menu_title": "🛡 <b>Control panel</b>",
        "menu_sub": "<i>choose an action</i>",
        "btn_add_chat": "➕ Add to chat",
        "btn_profile": "👤 Profile",
        "btn_my_chats": "📋 My chats",
        "btn_admin_panel": "⚙️ Admin panel",
        "btn_back": "⬅️ Back",
        "bot_disabled": "🔧 Bot temporarily disabled.",
        "access_denied": "🚫 Access denied.",
        "request_new": "🔔 <b>New access request</b>",
        "request_sent": (
            "⏳ <b>Access not granted</b>\n\n"
            "Request sent to administrator. Wait for approval."
        ),
        "welcome": (
            "👋 Welcome.\n"
            "Add the bot to a chat and send /biv start 60."
        ),
        "profile_title": "👤 <b>Profile</b>",
        "profile_id": "🆔 ID",
        "profile_name": "📛 Name",
        "profile_username": "🔗 Username",
        "profile_role": "🎭 Role",
        "profile_chats": "📋 Chats with bot",
        "role_superadmin": "👑 Super admin",
        "role_admin": "🛡 Admin",
        "role_banned": "🚫 Banned",
        "role_user": "✅ User",
        "role_pending": "⏳ Pending",
        "admin_panel_title": "⚙️ <b>Admin panel</b>",
        "admin_panel_sub": "Choose a section 👇",
        "btn_users": "👥 Users",
        "btn_stats": "📊 Statistics",
        "btn_settings": "⚙️ Settings",
        "btn_backup": "💾 Backup",
        "users_title": "👥 <b>Users</b>",
        "users_sub": "Choose a section 👇",
        "btn_all_users": "📜 All users",
        "btn_pending": "⏳ Pending approval",
        "btn_banned": "🚫 Banned",
        "btn_admins": "🛡 Admins",
        "pending_title": "⏳ <b>Pending approval</b>",
        "pending_empty": "⏳ <b>Pending approval:</b>\n\nnobody",
        "banned_title": "🚫 <b>Banned:</b>",
        "banned_empty": "🚫 <b>Banned:</b>\n\nnobody",
        "admins_title": "🛡 <b>Admins:</b>",
        "admins_super": "👑 Super admin",
        "admins_empty": "<i>no regular admins</i>",
        "all_users_title": "📜 <b>All users:</b>",
        "all_users_empty": "📜 <b>All users:</b>\n\nnobody yet",
        "btn_approve": "✅ Approve",
        "btn_ban": "🚫 Ban",
        "btn_unban": "♻️ Unban",
        "btn_makeadmin": "🛡 Make admin",
        "btn_removeadmin": "🗑 Remove admin",
        "btn_delete": "🗑 Delete",
        "done": "Done.",
        "no_access": "⛔ No access.",
        "only_superadmin": "⛔ Super admin only.",
        "cant_touch_super": "⛔ Can't touch super admin.",
        "user_not_found": "User not found.",
        "id_error": "ID error.",
        "notify_approved": "✅ Access granted.",
        "notify_banned": "🚫 You are banned.",
        "notify_unbanned": "♻️ You are unbanned.",
        "notify_makeadmin": "🛡 You've been promoted to admin.",
        "notify_removeadmin": "🗑 Admin rights removed.",
        "stats_title": "📊 <b>Bot statistics</b>",
        "stats_users": "👥 Total users",
        "stats_pending": "⏳ Pending",
        "stats_banned": "🚫 Banned",
        "stats_admins": "🛡 Admins",
        "stats_chats": "📋 Chats",
        "stats_wins": "🎮 Total wins",
        "settings_title": "⚙️ <b>Bot settings</b>",
        "settings_sub": "Change parameters below 👇",
        "btn_antiflood": "🚫 Antiflood",
        "btn_badwords": "🚫 Bad words list",
        "btn_lang": "🌐 Language",
        "btn_notify": "🔔 Notifications",
        "lang_title": "🌐 <b>Language</b>",
        "lang_sub": "Choose language 👇",
        "lang_changed": "Language changed: {}",
        "notify_title": "🔔 <b>Notifications</b>",
        "notify_sub": "What to send to your DM 👇",
        "notify_joins": "➕ Chat joins",
        "notify_leaves": "➖ Chat leaves",
        "notify_requests": "🔔 Access requests",
        "notify_wins": "🏆 Game wins",
        "notify_updated": "Updated.",
        "words_title": "🚫 <b>Bad words list</b>",
        "words_empty": "List is empty.",
        "words_list": "🚫 Words:",
        "words_added": "✅ Added: <code>{}</code>",
        "words_deleted": "🗑 Deleted: <code>{}</code>",
        "words_exists": "Already exists or empty.",
        "words_not_found": "No such word.",
        "words_usage_add": "Usage: /addword word",
        "words_usage_del": "Usage: /delword word",
        "words_swear": "🚫 {}, don't swear.",
        "backup_title": "💾 <b>Backup</b>",
        "backup_sub": "Export saves all users, stats and chats to a server file.",
        "btn_export": "📤 Export to file",
        "btn_import": "📥 Import from file",
        "btn_info": "ℹ️ About backup",
        "backup_saved": "✅ <b>Backup saved</b>",
        "backup_restored": "✅ <b>Backup restored</b>",
        "backup_error_export": "❌ Backup error:",
        "backup_error_import": "❌ Import error:",
        "backup_no_file": "No file.",
        "backup_info_title": "ℹ️ <b>About backup</b>",
        "backup_file": "File",
        "backup_exists": "Exists",
        "backup_size": "Size",
        "backup_bytes": "bytes",
        "chats_title": "📋 <b>Chats:</b>",
        "chats_empty": "📋 <b>Chats:</b>\n\nempty",
        "add_chat_title": "➕ <b>How to add bot to a chat</b>",
        "add_chat_1": "<b>1.</b> Copy the bot username:",
        "add_chat_2": "<b>2.</b> Chat → Manage → Add member.",
        "add_chat_3": (
            "<b>3.</b> Manage → Administrators → grant rights:\n"
            "     • Delete messages\n"
            "     • Pin messages"
        ),
        "add_chat_4": "<b>4.</b> @BotFather → Group Privacy → Turn off",
        "add_chat_5": "<b>5.</b> In chat: <code>/biv start 60</code>",
        "chat_added_title": "✅ <b>Bot added to chat</b>",
        "chat_removed_title": "❌ <b>Bot removed from chat</b>",
        "chat_denied_title": "🚫 <b>Attempt to add without access</b>",
        "chat_denied_msg": "⛔ No access. Bot leaves the chat.",
        "chat_name": "📌 Name",
        "chat_id": "🆔 Chat ID",
        "chat_added_by": "👤 Added by",
        "game_started": "🎮 Game started",
        "game_seconds": "⏱ {} sec",
        "game_hint": "Send a message — become the leader.",
        "game_stopped": "🛑 Game stopped.",
        "game_already": "Game is already running.",
        "game_not_running": "Game is not running.",
        "game_invalid_duration": "Time must be between {} and {} sec.",
        "game_bad_number": "Time must be a number. Example: /biv start 60",
        "game_flood": "🔄 Interrupted!",
        "game_new_leader": "New leader",
        "game_time_left": "Time left",
        "game_winner": "🏆 Winner",
        "game_message": "Message",
        "top_title": "🏆 Top players:",
        "top_empty": "📊 No wins in this chat yet.",
        "top_players": "Total players",
        "my_stats": "📈 Stats of {}",
        "my_stats_wins": "Wins",
        "my_stats_place": "Place",
        "my_stats_zero": "{} has 0 wins yet.",
        "reset_done": "🧹 Chat stats reset.",
        "cmd_makeadmin_usage": "Usage: /makeadmin <user_id>",
        "cmd_unmakeadmin_usage": "Usage: /unmakeadmin <user_id>",
        "cmd_ban_usage": "Usage: /ban <user_id>",
        "cmd_unban_usage": "Usage: /unban <user_id>",
        "cmd_approve_usage": "Usage: /approve <user_id>",
        "cmd_id_number": "ID must be a number.",
        "cmd_made_admin": "✅ {} is now admin.",
        "cmd_removed_admin": "🗑 {} is no longer admin.",
        "cmd_banned": "🚫 {} banned.",
        "cmd_unbanned": "♻️ {} unbanned.",
        "cmd_approved": "✅ {} approved.",
        "cmd_user_first_start": "User not found (they must send /start first).",
        "user_card": (
            "👤 <b>User</b>\n\n"
            "📛 Name: {name}\n"
            "🔗 Username: {username}\n"
            "🆔 ID: <code>{user_id}</code>\n"
            "🎭 Status: {status}"
        ),
        "status_admin": "🛡 Admin",
        "status_banned": "🚫 Banned",
        "status_user": "✅ User",
        "status_pending": "⏳ Pending",
        "status_superadmin": "👑 Super admin",
        "quick_ban_title": "🚫 <b>Who to ban?</b>\n\nPick a user:",
        "quick_ban_empty": "🚫 Nobody to ban — no active users.",
        "quick_unban_title": "♻️ <b>Who to unban?</b>\n\nPick a user:",
        "quick_unban_empty": "♻️ Nobody to unban — no banned users.",
        "quick_add_admin_title": "🛡 <b>Who to make admin?</b>\n\nPick a user:",
        "quick_add_admin_empty": "🛡 Nobody to promote — no approved users.",
        "quick_del_admin_title": "🗑 <b>Who to demote?</b>\n\nPick an admin:",
        "quick_del_admin_empty": "🗑 No regular admins.",
    },
}


# ─────────────────────────── Исключения ───────────────────────────

class GameError(Exception):
    pass


class GameAlreadyRunning(GameError):
    pass


class GameNotRunning(GameError):
    pass


class InvalidDuration(GameError):
    pass


# ─────────────────────────── Настройки ───────────────────────────

@dataclass
class Settings:
    enabled: bool = True
    antiflood: bool = True
    bad_words: list[str] = field(default_factory=lambda: ["мат1", "мат2", "мат3"])
    language: str = "ru"
    notify_joins: bool = True
    notify_leaves: bool = True
    notify_requests: bool = True
    notify_wins: bool = False

    def is_bad_word(self, text: str) -> bool:
        low = text.lower()
        return any(w.lower() in low for w in self.bad_words if w)


# ─────────────────────────── Пользователи ───────────────────────────

@dataclass
class UserInfo:
    user_id: int
    name: str
    username: Optional[str] = None
    approved: bool = False
    banned: bool = False
    is_admin: bool = False


class UserStore:
    def __init__(self, superadmin_id: int) -> None:
        self._users: dict[int, UserInfo] = {}
        self._superadmin_id = superadmin_id

    def touch(self, user: types.User) -> UserInfo:
        info = self._users.get(user.id)
        if info is None:
            info = UserInfo(
                user_id=user.id,
                name=user.full_name,
                username=user.username,
                approved=(user.id == self._superadmin_id),
                is_admin=(user.id == self._superadmin_id),
            )
            self._users[user.id] = info
        else:
            info.name = user.full_name
            info.username = user.username
        return info

    def get(self, user_id: int) -> Optional[UserInfo]:
        return self._users.get(user_id)

    def is_superadmin(self, user_id: int) -> bool:
        return user_id == self._superadmin_id

    def is_admin(self, user_id: int) -> bool:
        if self.is_superadmin(user_id):
            return True
        info = self._users.get(user_id)
        return info is not None and info.is_admin and not info.banned

    def has_access(self, user_id: int) -> bool:
        if self.is_superadmin(user_id):
            return True
        info = self._users.get(user_id)
        if info is None:
            return False
        return info.approved and not info.banned

    def approve(self, uid: int) -> bool:
        info = self._users.get(uid)
        if info is None:
            return False
        info.approved = True
        info.banned = False
        return True

    def ban(self, uid: int) -> bool:
        info = self._users.get(uid)
        if info is None:
            return False
        info.banned = True
        info.approved = False
        info.is_admin = False
        return True

    def unban(self, uid: int) -> bool:
        info = self._users.get(uid)
        if info is None:
            return False
        info.banned = False
        return True

    def make_admin(self, uid: int) -> bool:
        if self.is_superadmin(uid):
            return False
        info = self._users.get(uid)
        if info is None:
            return False
        info.is_admin = True
        info.approved = True
        info.banned = False
        return True

    def remove_admin(self, uid: int) -> bool:
        info = self._users.get(uid)
        if info is None:
            return False
        info.is_admin = False
        return True

    def remove_user(self, uid: int) -> bool:
        if self.is_superadmin(uid):
            return False
        if uid in self._users:
            del self._users[uid]
            return True
        return False

    def all_users(self) -> list[UserInfo]:
        return list(self._users.values())

    def pending_users(self) -> list[UserInfo]:
        return [
            u for u in self._users.values()
            if not u.approved and not u.banned and not self.is_superadmin(u.user_id)
        ]

    def banned_users(self) -> list[UserInfo]:
        return [u for u in self._users.values() if u.banned]

    def admins(self) -> list[UserInfo]:
        return [u for u in self._users.values() if u.is_admin and not u.banned]

    def load(self, data: dict[int, UserInfo]) -> None:
        self._users = data


# ─────────────────────────── Игровые модели ───────────────────────────

@dataclass
class Leader:
    user_id: int
    name: str
    text: str
    message_id: int


@dataclass
class PlayerStat:
    user_id: int
    name: str
    wins: int = 0


class Stats:
    def __init__(self) -> None:
        self._data: dict[int, dict[int, PlayerStat]] = {}

    def add_win(self, chat_id: int, user_id: int, name: str) -> None:
        chat = self._data.setdefault(chat_id, {})
        stat = chat.get(user_id)
        if stat is None:
            stat = PlayerStat(user_id=user_id, name=name, wins=0)
            chat[user_id] = stat
        stat.name = name
        stat.wins += 1

    def top(self, chat_id: int, limit: int = 10) -> list[PlayerStat]:
        chat = self._data.get(chat_id, {})
        return sorted(chat.values(), key=lambda s: s.wins, reverse=True)[:limit]

    def get(self, chat_id: int, user_id: int) -> Optional[PlayerStat]:
        return self._data.get(chat_id, {}).get(user_id)

    def reset(self, chat_id: int) -> None:
        self._data.pop(chat_id, None)

    def total_players(self, chat_id: int) -> int:
        return len(self._data.get(chat_id, {}))

    def total_games(self) -> int:
        return sum(len(c) for c in self._data.values())

    def export(self) -> dict:
        out: dict[str, dict] = {}
        for chat_id, chat in self._data.items():
            out[str(chat_id)] = {str(uid): asdict(st) for uid, st in chat.items()}
        return out

    def import_(self, raw: dict) -> None:
        self._data = {}
        for chat_id_str, chat in raw.items():
            chat_id = int(chat_id_str)
            self._data[chat_id] = {}
            for uid_str, st in chat.items():
                uid = int(uid_str)
                self._data[chat_id][uid] = PlayerStat(**st)


@dataclass
class Game:
    chat_id: int
    duration: int = DEFAULT_DURATION
    leader: Optional[Leader] = None
    leader_message_id: Optional[int] = None
    remaining: int = 0                                  # ← текущее оставшееся время
    _timer: Optional[asyncio.Task[None]] = field(default=None, repr=False)
    _started: bool = field(default=False, repr=False)

    @property
    def running(self) -> bool:
        return self._timer is not None and not self._timer.done()

    @property
    def active(self) -> bool:
        return self._started

    def set_duration(self, seconds: int) -> None:
        if not MIN_DURATION <= seconds <= MAX_DURATION:
            raise InvalidDuration(
                t("game_invalid_duration").format(MIN_DURATION, MAX_DURATION)
            )
        self.duration = seconds

    def begin(self, duration: Optional[int]) -> None:
        if self._started:
            raise GameAlreadyRunning(t("game_already"))
        if duration is not None:
            self.set_duration(duration)
        self.leader = None
        self.leader_message_id = None
        self.remaining = self.duration                          # ← старт с полного
        self._timer = None
        self._started = True

    async def end(self, bot: Bot) -> None:
        if not self._started:
            raise GameNotRunning(t("game_not_running"))
        self._cancel_timer()
        self.leader = None
        self.leader_message_id = None
        self.remaining = 0
        self._started = False

    async def promote(self, bot: Bot, leader: Leader) -> None:
        """Перебитие: меняем лидера, таймер ПРОДОЛЖАЕТСЯ с текущего remaining."""
        old_msg_id = self.leader_message_id

        # НЕ отменяем таймер! Просто меняем лидера.
        self.leader = leader

        # Удаляем старое сообщение (если было)
        if old_msg_id is not None:
            try:
                await bot.delete_message(self.chat_id, old_msg_id)
            except TelegramBadRequest as e:
                log.debug("Не удалил старое сообщение %s: %s", old_msg_id, e)

        # Шлём новое сообщение с ТЕКУЩИМ remaining
        text = (
            f"{t('game_flood')}\n\n"
            f"{t('game_new_leader')}: {leader.name}\n"
            f"{t('game_time_left')}: {self.remaining}"
        )

        try:
            msg = await bot.send_message(chat_id=self.chat_id, text=text)
            self.leader_message_id = msg.message_id
        except TelegramBadRequest as e:
            log.warning("Не смог отправить сообщение: %s", e)
            self.leader_message_id = None

        # Если таймер по какой-то причине не идёт — запускаем
        if not self.running:
            self._timer = asyncio.create_task(
                self._run_timer(bot), name=f"game-{self.chat_id}"
            )

    async def _run_timer(self, bot: Bot) -> None:
        try:
            while self.remaining > 0:
                await asyncio.sleep(1)
                self.remaining -= 1

                if self.leader is None or self.leader_message_id is None:
                    # Лидера нет — заканчиваем
                    return

                if self.remaining % TIMER_UPDATE_EVERY != 0 and self.remaining != 0:
                    continue

                text = (
                    f"{t('game_flood')}\n\n"
                    f"{t('game_new_leader')}: {self.leader.name}\n"
                    f"{t('game_time_left')}: {self.remaining}"
                )
                try:
                    await bot.edit_message_text(
                        chat_id=self.chat_id,
                        message_id=self.leader_message_id,
                        text=text,
                    )
                except TelegramRetryAfter as e:
                    log.warning("Flood control: ждём %s сек", e.retry_after)
                    await asyncio.sleep(e.retry_after)
                except TelegramBadRequest:
                    pass

            if self.leader is None:
                return

            winner = self.leader
            final_text = (
                f"{t('game_winner')}: {winner.name}\n"
                f"{t('game_message')}: «{winner.text}»"
            )

            if self.leader_message_id is not None:
                try:
                    await bot.edit_message_text(
                        chat_id=self.chat_id,
                        message_id=self.leader_message_id,
                        text=final_text,
                    )
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    try:
                        await bot.edit_message_text(
                            chat_id=self.chat_id,
                            message_id=self.leader_message_id,
                            text=final_text,
                        )
                    except Exception:
                        pass
                except TelegramBadRequest:
                    try:
                        await bot.send_message(chat_id=self.chat_id, text=final_text)
                    except TelegramBadRequest:
                        pass

            # 🏆 Закрепляем сообщение победителя
            if self.leader_message_id is not None:
                try:
                    await bot.pin_chat_message(
                        chat_id=self.chat_id,
                        message_id=self.leader_message_id,
                        disable_notification=True,
                    )
                except TelegramBadRequest as e:
                    log.warning("Не смог закрепить победителя в %s: %s", self.chat_id, e)

            stats.add_win(self.chat_id, winner.user_id, winner.name)
            log.info("Победа в чате %s: %s", self.chat_id, winner.name)

            if settings.notify_wins:
                try:
                    await bot.send_message(
                        chat_id=SUPERADMIN_ID,
                        text=(
                            f"{t('game_winner')}\n"
                            f"{t('chat_id')}: <code>{self.chat_id}</code>\n"
                            f"{winner.name}"
                        ),
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

            self.leader = None
            self.leader_message_id = None
            self.remaining = 0
            self._timer = None
            self._started = False

        except asyncio.CancelledError:
            log.info("Таймер чата %s отменён", self.chat_id)
            raise

    def _cancel_timer(self) -> None:
        if self.running and self._timer is not None:
            self._timer.cancel()
        self._timer = None


class GameManager:
    def __init__(self) -> None:
        self._games: dict[int, Game] = {}

    def get(self, chat_id: int) -> Game:
        game = self._games.get(chat_id)
        if game is None:
            game = Game(chat_id=chat_id)
            self._games[chat_id] = game
        return game

    def begin(self, chat_id: int, duration: Optional[int]) -> Game:
        game = self.get(chat_id)
        game.begin(duration)
        return game

    async def end(self, bot: Bot, chat_id: int) -> None:
        await self.get(chat_id).end(bot)


# ─────────────────────────── Хранилища ───────────────────────────

router = Router()
manager = GameManager()
stats = Stats()
users = UserStore(SUPERADMIN_ID)
settings = Settings()

known_chats: dict[int, str] = {}


# ─────────────────────────── Локализация ───────────────────────────

def t(key: str) -> str:
    lang = settings.language if settings.language in STRINGS else "ru"
    return STRINGS[lang].get(key, STRINGS["ru"].get(key, key))


# ─────────────────────────── Клавиатуры ───────────────────────────

def kb_main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=t("btn_add_chat"), callback_data="admin:add")],
        [
            InlineKeyboardButton(text=t("btn_profile"),  callback_data="profile"),
            InlineKeyboardButton(text=t("btn_my_chats"), callback_data="admin:chats"),
        ],
    ]
    if is_admin:
        rows.append([
            InlineKeyboardButton(text=t("btn_admin_panel"), callback_data="admin:panel"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_panel(is_super: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if is_super:
        rows.append([
            InlineKeyboardButton(text="🚫 Забанить",      callback_data="quick:ban"),
            InlineKeyboardButton(text="♻️ Разбанить",    callback_data="quick:unban"),
        ])
        rows.append([
            InlineKeyboardButton(text="🛡 Добавить админа", callback_data="quick:add_admin"),
            InlineKeyboardButton(text="🗑 Удалить админа",  callback_data="quick:del_admin"),
        ])
    rows.append([InlineKeyboardButton(text=t("btn_users"),    callback_data="admin:users")])
    rows.append([InlineKeyboardButton(text=t("btn_stats"),    callback_data="admin:stats")])
    rows.append([InlineKeyboardButton(text=t("btn_settings"), callback_data="admin:settings")])
    rows.append([InlineKeyboardButton(text=t("btn_backup"),   callback_data="admin:backup")])
    rows.append([InlineKeyboardButton(text=t("btn_back"),     callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_settings_menu() -> InlineKeyboardMarkup:
    def mark(flag: bool) -> str:
        return "✅" if flag else "❌"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{mark(settings.antiflood)} {t('btn_antiflood')}",
                callback_data="set:toggle:antiflood",
            )],
            [InlineKeyboardButton(
                text=f"{t('btn_badwords')} ({len(settings.bad_words)})",
                callback_data="set:words",
            )],
            [InlineKeyboardButton(
                text=f"{t('btn_lang')}: {settings.language.upper()}",
                callback_data="set:lang",
            )],
            [InlineKeyboardButton(
                text=t("btn_notify"),
                callback_data="set:notify",
            )],
            [InlineKeyboardButton(text=t("btn_back"), callback_data="admin:panel")],
        ]
    )


def kb_lang_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=("✅ " if settings.language == "ru" else "") + "🇷🇺 Русский",
                callback_data="set:lang:ru",
            )],
            [InlineKeyboardButton(
                text=("✅ " if settings.language == "en" else "") + "🇬🇧 English",
                callback_data="set:lang:en",
            )],
            [InlineKeyboardButton(text=t("btn_back"), callback_data="admin:settings")],
        ]
    )


def kb_notify_menu() -> InlineKeyboardMarkup:
    def mark(flag: bool) -> str:
        return "✅" if flag else "❌"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{mark(settings.notify_joins)} {t('notify_joins')}",
                callback_data="set:notify:toggle:joins",
            )],
            [InlineKeyboardButton(
                text=f"{mark(settings.notify_leaves)} {t('notify_leaves')}",
                callback_data="set:notify:toggle:leaves",
            )],
            [InlineKeyboardButton(
                text=f"{mark(settings.notify_requests)} {t('notify_requests')}",
                callback_data="set:notify:toggle:requests",
            )],
            [InlineKeyboardButton(
                text=f"{mark(settings.notify_wins)} {t('notify_wins')}",
                callback_data="set:notify:toggle:wins",
            )],
            [InlineKeyboardButton(text=t("btn_back"), callback_data="admin:settings")],
        ]
    )


def kb_backup_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_export"), callback_data="backup:export")],
            [InlineKeyboardButton(text=t("btn_import"), callback_data="backup:import")],
            [InlineKeyboardButton(text=t("btn_info"),   callback_data="backup:info")],
            [InlineKeyboardButton(text=t("btn_back"),   callback_data="admin:panel")],
        ]
    )


def kb_users_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_all_users"), callback_data="users:all")],
            [InlineKeyboardButton(text=t("btn_pending"),   callback_data="users:pending")],
            [InlineKeyboardButton(text=t("btn_banned"),    callback_data="users:banned")],
            [InlineKeyboardButton(text=t("btn_admins"),    callback_data="users:admins")],
            [InlineKeyboardButton(text=t("btn_back"),      callback_data="admin:panel")],
        ]
    )


def _status_of(u: UserInfo) -> str:
    if users.is_superadmin(u.user_id):
        return t("status_superadmin")
    if u.banned:
        return t("status_banned")
    if u.is_admin:
        return t("status_admin")
    if u.approved:
        return t("status_user")
    return t("status_pending")


def kb_user_card(u: UserInfo) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if not u.approved and not u.banned:
        rows.append([InlineKeyboardButton(
            text=t("btn_approve"),
            callback_data=f"user:approve:{u.user_id}",
        )])

    if u.banned:
        rows.append([InlineKeyboardButton(
            text=t("btn_unban"),
            callback_data=f"user:unban:{u.user_id}",
        )])
    else:
        rows.append([InlineKeyboardButton(
            text=t("btn_ban"),
            callback_data=f"user:ban:{u.user_id}",
        )])

    if users.is_superadmin(u.user_id):
        pass
    elif u.is_admin:
        rows.append([InlineKeyboardButton(
            text=t("btn_removeadmin"),
            callback_data=f"user:removeadmin:{u.user_id}",
        )])
    elif not u.banned:
        rows.append([InlineKeyboardButton(
            text=t("btn_makeadmin"),
            callback_data=f"user:makeadmin:{u.user_id}",
        )])

    if not users.is_superadmin(u.user_id):
        rows.append([InlineKeyboardButton(
            text=t("btn_delete"),
            callback_data=f"user:remove:{u.user_id}",
        )])

    rows.append([InlineKeyboardButton(text=t("btn_back"), callback_data="admin:users")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_users_list(items: list[UserInfo], kind: str, page: int, per_page: int = 8) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    start = page * per_page
    chunk = items[start : start + per_page]

    for u in chunk:
        name = _user_link(u)
        status = _status_of(u)
        rows.append([InlineKeyboardButton(
            text=f"{status} {name}",
            callback_data=f"ucard:{kind}:{u.user_id}",
        )])

    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"ulist:{kind}:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"ulist:{kind}:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text=t("btn_back"), callback_data="admin:users")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_quick_pick(items: list[UserInfo], kind: str, page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    start = page * per_page
    chunk = items[start : start + per_page]

    for u in chunk:
        name = _user_link(u)
        status = _status_of(u)
        rows.append([InlineKeyboardButton(
            text=f"{status} {name}",
            callback_data=f"quickpick:{kind}:{u.user_id}",
        )])

    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"quickpage:{kind}:{page - 1}"))
        nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page + 1 < total_pages:
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"quickpage:{kind}:{page + 1}"))
        rows.append(nav)

    rows.append([InlineKeyboardButton(text=t("btn_back"), callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_back_to_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_back"), callback_data="admin:panel")]]
    )


def kb_back_to_users() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_back"), callback_data="admin:users")]]
    )


def kb_back_to_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_back"), callback_data="admin:settings")]]
    )


def kb_back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_back"), callback_data="menu")]]
    )


def kb_request_actions(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_approve"), callback_data=f"user:approve:{user_id}"),
                InlineKeyboardButton(text=t("btn_ban"),     callback_data=f"user:ban:{user_id}"),
            ],
            [
                InlineKeyboardButton(text=t("btn_makeadmin"), callback_data=f"user:makeadmin:{user_id}"),
            ],
        ]
    )


# ─────────────────────────── Утилиты ───────────────────────────

def _parse_duration(args: list[str]) -> Optional[int]:
    if len(args) < 3:
        return None
    try:
        return int(args[2])
    except ValueError as e:
        raise InvalidDuration(t("game_bad_number")) from e


def _medal(i: int) -> str:
    return {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, f"{i + 1}.")


def _user_link(u: UserInfo) -> str:
    return f"@{u.username}" if u.username else u.name


def _profile_text(user: types.User, info: UserInfo) -> str:
    total_chats = len(known_chats)
    username = f"@{user.username}" if user.username else "—"
    if users.is_superadmin(user.id):
        role = t("role_superadmin")
    elif info.is_admin:
        role = t("role_admin")
    elif info.banned:
        role = t("role_banned")
    elif info.approved:
        role = t("role_user")
    else:
        role = t("role_pending")
    return (
        f"{t('profile_title')}\n\n"
        f"{t('profile_id')}: <code>{user.id}</code>\n"
        f"{t('profile_name')}: {user.full_name}\n"
        f"{t('profile_username')}: {username}\n"
        f"{t('profile_role')}: {role}\n\n"
        f"{t('profile_chats')}: <b>{total_chats}</b>"
    )


def _user_card_text(u: UserInfo) -> str:
    username = f"@{u.username}" if u.username else "—"
    status = _status_of(u)
    return t("user_card").format(
        name=u.name,
        username=username,
        user_id=u.user_id,
        status=status,
    )


def _is_admin(user: Optional[types.User]) -> bool:
    return user is not None and users.is_admin(user.id)


def _has_access(user: Optional[types.User]) -> bool:
    return user is not None and users.has_access(user.id)


def _menu_text() -> str:
    return f"{t('menu_title')}\n{t('menu_sub')}"


# ─────────────────────────── /start ───────────────────────────

@router.message(Command("start"))
async def cmd_start(message: types.Message, bot: Bot) -> None:
    user = message.from_user
    if user is None:
        return
    info = users.touch(user)

    if message.chat.type != "private":
        return

    if not settings.enabled and not users.is_superadmin(user.id):
        await message.answer(t("bot_disabled"))
        return

    if info.banned:
        await message.answer(t("access_denied"))
        return

    if not info.approved:
        if settings.notify_requests:
            try:
                await bot.send_message(
                    chat_id=SUPERADMIN_ID,
                    text=(
                        f"{t('request_new')}\n\n"
                        f"👤 {_user_link(info)}\n"
                        f"📛 {info.name}\n"
                        f"🆔 <code>{info.user_id}</code>"
                    ),
                    parse_mode="HTML",
                    reply_markup=kb_request_actions(info.user_id),
                )
            except Exception as e:
                log.warning("Не смог уведомить: %s", e)

        await message.answer(t("request_sent"), parse_mode="HTML")
        return

    await message.answer(
        _menu_text(),
        parse_mode="HTML",
        reply_markup=kb_main_menu(is_admin=_is_admin(user)),
    )


# ─────────────────────────── Callback: меню ───────────────────────────

@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery) -> None:
    if not _has_access(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    await call.message.edit_text(
        _menu_text(),
        parse_mode="HTML",
        reply_markup=kb_main_menu(is_admin=_is_admin(call.from_user)),
    )
    await call.answer()


@router.callback_query(F.data == "profile")
async def cb_profile(call: CallbackQuery) -> None:
    if not _has_access(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    info = users.touch(call.from_user)
    await call.message.edit_text(
        _profile_text(call.from_user, info),
        parse_mode="HTML",
        reply_markup=kb_back_to_menu(),
    )
    await call.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery) -> None:
    await call.answer()


# ─────────────────────────── Callback: админка ───────────────────────────

@router.callback_query(F.data == "admin:panel")
async def cb_admin_panel(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    is_super = users.is_superadmin(call.from_user.id)
    await call.message.edit_text(
        f"{t('admin_panel_title')}\n\n{t('admin_panel_sub')}",
        parse_mode="HTML",
        reply_markup=kb_admin_panel(is_super=is_super),
    )
    await call.answer()


@router.callback_query(F.data == "admin:add")
async def cb_admin_add(call: CallbackQuery) -> None:
    if not _has_access(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    text = (
        f"{t('add_chat_title')}\n\n"
        f"{t('add_chat_1')}\n"
        f"<code>@{BOT_USERNAME}</code>\n\n"
        f"{t('add_chat_2')}\n\n"
        f"{t('add_chat_3')}\n\n"
        f"{t('add_chat_4')}\n\n"
        f"{t('add_chat_5')}"
    )
    await call.message.edit_text(
        text, parse_mode="HTML", reply_markup=kb_back_to_menu(),
        disable_web_page_preview=True,
    )
    await call.answer()


@router.callback_query(F.data == "admin:chats")
async def cb_admin_chats(call: CallbackQuery) -> None:
    if not _has_access(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    if not known_chats:
        text = t("chats_empty")
    else:
        lines = [t("chats_title"), ""]
        for chat_id, title in known_chats.items():
            lines.append(f"• {title}\n  <code>{chat_id}</code>")
        text = "\n".join(lines)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb_back_to_menu())
    await call.answer()


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    text = (
        f"{t('stats_title')}\n\n"
        f"{t('stats_users')}: <b>{len(users.all_users())}</b>\n"
        f"{t('stats_pending')}: <b>{len(users.pending_users())}</b>\n"
        f"{t('stats_banned')}: <b>{len(users.banned_users())}</b>\n"
        f"{t('stats_admins')}: <b>{len(users.admins())}</b>\n\n"
        f"{t('stats_chats')}: <b>{len(known_chats)}</b>\n"
        f"{t('stats_wins')}: <b>{stats.total_games()}</b>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb_back_to_panel())
    await call.answer()


# ─────────────────────────── Callback: настройки ───────────────────────────

@router.callback_query(F.data == "admin:settings")
async def cb_settings(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    await call.message.edit_text(
        f"{t('settings_title')}\n\n{t('settings_sub')}",
        parse_mode="HTML",
        reply_markup=kb_settings_menu(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("set:toggle:"))
async def cb_set_toggle(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    key = call.data.split(":")[2]
    if key == "antiflood":
        settings.antiflood = not settings.antiflood
    if call.message is not None:
        try:
            await call.message.edit_reply_markup(reply_markup=kb_settings_menu())
        except TelegramBadRequest:
            pass
    await call.answer(t("notify_updated"))


@router.callback_query(F.data == "set:lang")
async def cb_set_lang(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    await call.message.edit_text(
        f"{t('lang_title')}\n\n{t('lang_sub')}",
        parse_mode="HTML",
        reply_markup=kb_lang_menu(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("set:lang:"))
async def cb_set_lang_apply(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    lang = call.data.split(":")[2]
    if lang in ("ru", "en"):
        settings.language = lang
    if call.message is not None:
        try:
            await call.message.edit_text(
                f"{t('lang_title')}\n\n{t('lang_sub')}",
                parse_mode="HTML",
                reply_markup=kb_lang_menu(),
            )
        except TelegramBadRequest:
            pass
    await call.answer(t("lang_changed").format(lang.upper()))


@router.callback_query(F.data == "set:notify")
async def cb_set_notify(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    await call.message.edit_text(
        f"{t('notify_title')}\n\n{t('notify_sub')}",
        parse_mode="HTML",
        reply_markup=kb_notify_menu(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("set:notify:toggle:"))
async def cb_set_notify_toggle(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    key = call.data.split(":")[3]
    if key == "joins":
        settings.notify_joins = not settings.notify_joins
    elif key == "leaves":
        settings.notify_leaves = not settings.notify_leaves
    elif key == "requests":
        settings.notify_requests = not settings.notify_requests
    elif key == "wins":
        settings.notify_wins = not settings.notify_wins
    if call.message is not None:
        try:
            await call.message.edit_reply_markup(reply_markup=kb_notify_menu())
        except TelegramBadRequest:
            pass
    await call.answer(t("notify_updated"))


@router.callback_query(F.data == "set:words")
async def cb_set_words(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    words = ", ".join(settings.bad_words) if settings.bad_words else "—"
    await call.message.edit_text(
        f"{t('words_title')}\n\n"
        f"<code>{words}</code>\n\n"
        f"<code>/addword слово</code>\n"
        f"<code>/delword слово</code>\n"
        f"<code>/words</code>",
        parse_mode="HTML",
        reply_markup=kb_back_to_settings(),
    )
    await call.answer()


# ─────────────────────────── Callback: бэкап ───────────────────────────

@router.callback_query(F.data == "admin:backup")
async def cb_backup(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    await call.message.edit_text(
        f"{t('backup_title')}\n\n{t('backup_sub')}",
        parse_mode="HTML",
        reply_markup=kb_backup_menu(),
    )
    await call.answer()


@router.callback_query(F.data == "backup:export")
async def cb_backup_export(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    try:
        data = {
            "users": [asdict(u) for u in users.all_users()],
            "chats": {str(k): v for k, v in known_chats.items()},
            "stats": stats.export(),
            "settings": {
                "enabled": settings.enabled,
                "antiflood": settings.antiflood,
                "bad_words": settings.bad_words,
                "language": settings.language,
                "notify_joins": settings.notify_joins,
                "notify_leaves": settings.notify_leaves,
                "notify_requests": settings.notify_requests,
                "notify_wins": settings.notify_wins,
            },
        }
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if call.message is not None:
            await call.message.edit_text(
                f"{t('backup_saved')}\n\n"
                f"{t('backup_file')}: <code>{BACKUP_FILE}</code>\n"
                f"{len(data['users'])} / {len(data['chats'])}",
                parse_mode="HTML",
                reply_markup=kb_backup_menu(),
            )
    except Exception as e:
        log.exception("Ошибка бэкапа")
        if call.message is not None:
            await call.message.edit_text(
                f"{t('backup_error_export')} <code>{e}</code>",
                parse_mode="HTML",
                reply_markup=kb_backup_menu(),
            )
    await call.answer()


@router.callback_query(F.data == "backup:import")
async def cb_backup_import(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if not os.path.exists(BACKUP_FILE):
        await call.answer(t("backup_no_file"), show_alert=True)
        return
    try:
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        loaded_users: dict[int, UserInfo] = {}
        for u in data.get("users", []):
            info = UserInfo(**u)
            loaded_users[info.user_id] = info
        users.load(loaded_users)

        known_chats.clear()
        for k, v in data.get("chats", {}).items():
            known_chats[int(k)] = v

        stats.import_(data.get("stats", {}))

        s = data.get("settings", {})
        settings.enabled = s.get("enabled", True)
        settings.antiflood = s.get("antiflood", True)
        settings.bad_words = s.get("bad_words", settings.bad_words)
        settings.language = s.get("language", "ru")
        settings.notify_joins = s.get("notify_joins", True)
        settings.notify_leaves = s.get("notify_leaves", True)
        settings.notify_requests = s.get("notify_requests", True)
        settings.notify_wins = s.get("notify_wins", False)

        if call.message is not None:
            await call.message.edit_text(
                f"{t('backup_restored')}\n\n"
                f"{len(loaded_users)} / {len(known_chats)}",
                parse_mode="HTML",
                reply_markup=kb_backup_menu(),
            )
    except Exception as e:
        log.exception("Ошибка импорта")
        if call.message is not None:
            await call.message.edit_text(
                f"{t('backup_error_import')} <code>{e}</code>",
                parse_mode="HTML",
                reply_markup=kb_backup_menu(),
            )
    await call.answer()


@router.callback_query(F.data == "backup:info")
async def cb_backup_info(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    exists = os.path.exists(BACKUP_FILE)
    size = os.path.getsize(BACKUP_FILE) if exists else 0
    await call.message.edit_text(
        f"{t('backup_info_title')}\n\n"
        f"{t('backup_file')}: <code>{BACKUP_FILE}</code>\n"
        f"{t('backup_exists')}: {'✅' if exists else '❌'}\n"
        f"{t('backup_size')}: {size} {t('backup_bytes')}",
        parse_mode="HTML",
        reply_markup=kb_backup_menu(),
    )
    await call.answer()


# ─────────────────────────── Callback: юзеры ───────────────────────────

@router.callback_query(F.data == "admin:users")
async def cb_admin_users(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    await call.message.edit_text(
        f"{t('users_title')}\n\n{t('users_sub')}",
        parse_mode="HTML",
        reply_markup=kb_users_menu(),
    )
    await call.answer()


@router.callback_query(F.data == "users:pending")
async def cb_users_pending(call: CallbackQuery) -> None:
    await _show_list(call, "pending", 0)


@router.callback_query(F.data == "users:banned")
async def cb_users_banned(call: CallbackQuery) -> None:
    await _show_list(call, "banned", 0)


@router.callback_query(F.data == "users:admins")
async def cb_users_admins(call: CallbackQuery) -> None:
    await _show_list(call, "admins", 0)


@router.callback_query(F.data == "users:all")
async def cb_users_all(call: CallbackQuery) -> None:
    await _show_list(call, "all", 0)


@router.callback_query(F.data.startswith("ulist:"))
async def cb_users_list_page(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer()
        return
    kind = parts[1]
    try:
        page = int(parts[2])
    except ValueError:
        page = 0
    await _show_list(call, kind, page)


async def _show_list(call: CallbackQuery, kind: str, page: int) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return

    if kind == "pending":
        items = users.pending_users()
        title = t("pending_title")
        empty = t("pending_empty")
    elif kind == "banned":
        items = users.banned_users()
        title = t("banned_title")
        empty = t("banned_empty")
    elif kind == "admins":
        items = [u for u in users.admins() if u.user_id != SUPERADMIN_ID]
        title = t("admins_title")
        empty = t("admins_empty")
    elif kind == "all":
        items = [u for u in users.all_users() if u.user_id != SUPERADMIN_ID]
        title = t("all_users_title")
        empty = t("all_users_empty")
    else:
        await call.answer()
        return

    if not items:
        await call.message.edit_text(empty, parse_mode="HTML", reply_markup=kb_back_to_users())
        await call.answer()
        return

    await call.message.edit_text(
        title,
        parse_mode="HTML",
        reply_markup=kb_users_list(items, kind, page),
    )
    await call.answer()


@router.callback_query(F.data.startswith("ucard:"))
async def cb_user_card(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer()
        return
    kind = parts[1]
    try:
        uid = int(parts[2])
    except ValueError:
        await call.answer(t("id_error"), show_alert=True)
        return

    u = users.get(uid)
    if u is None:
        await call.answer(t("user_not_found"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return

    await call.message.edit_text(
        _user_card_text(u),
        parse_mode="HTML",
        reply_markup=kb_user_card(u),
    )
    await call.answer()


# ─────────────────────────── Callback: быстрые действия ───────────────────────────

@router.callback_query(F.data == "quick:ban")
async def cb_quick_ban(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    items = [
        u for u in users.all_users()
        if not u.banned and not users.is_superadmin(u.user_id)
    ]
    if not items:
        await call.message.edit_text(t("quick_ban_empty"), parse_mode="HTML", reply_markup=kb_back_to_panel())
        await call.answer()
        return
    await call.message.edit_text(
        t("quick_ban_title"), parse_mode="HTML",
        reply_markup=kb_quick_pick(items, "quick_ban"),
    )
    await call.answer()


@router.callback_query(F.data == "quick:unban")
async def cb_quick_unban(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    items = users.banned_users()
    if not items:
        await call.message.edit_text(t("quick_unban_empty"), parse_mode="HTML", reply_markup=kb_back_to_panel())
        await call.answer()
        return
    await call.message.edit_text(
        t("quick_unban_title"), parse_mode="HTML",
        reply_markup=kb_quick_pick(items, "quick_unban"),
    )
    await call.answer()


@router.callback_query(F.data == "quick:add_admin")
async def cb_quick_add_admin(call: CallbackQuery) -> None:
    if not users.is_superadmin(call.from_user.id):
        await call.answer(t("only_superadmin"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    items = [
        u for u in users.all_users()
        if u.approved and not u.banned and not u.is_admin
        and not users.is_superadmin(u.user_id)
    ]
    if not items:
        await call.message.edit_text(t("quick_add_admin_empty"), parse_mode="HTML", reply_markup=kb_back_to_panel())
        await call.answer()
        return
    await call.message.edit_text(
        t("quick_add_admin_title"), parse_mode="HTML",
        reply_markup=kb_quick_pick(items, "quick_add_admin"),
    )
    await call.answer()


@router.callback_query(F.data == "quick:del_admin")
async def cb_quick_del_admin(call: CallbackQuery) -> None:
    if not users.is_superadmin(call.from_user.id):
        await call.answer(t("only_superadmin"), show_alert=True)
        return
    if call.message is None:
        await call.answer()
        return
    items = [u for u in users.admins() if u.user_id != SUPERADMIN_ID]
    if not items:
        await call.message.edit_text(t("quick_del_admin_empty"), parse_mode="HTML", reply_markup=kb_back_to_panel())
        await call.answer()
        return
    await call.message.edit_text(
        t("quick_del_admin_title"), parse_mode="HTML",
        reply_markup=kb_quick_pick(items, "quick_del_admin"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("quickpage:"))
async def cb_quick_page(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer()
        return
    kind = parts[1]
    try:
        page = int(parts[2])
    except ValueError:
        page = 0

    if kind == "quick_ban":
        items = [u for u in users.all_users() if not u.banned and not users.is_superadmin(u.user_id)]
        title = t("quick_ban_title")
    elif kind == "quick_unban":
        items = users.banned_users()
        title = t("quick_unban_title")
    elif kind == "quick_add_admin":
        items = [u for u in users.all_users() if u.approved and not u.banned and not u.is_admin and not users.is_superadmin(u.user_id)]
        title = t("quick_add_admin_title")
    elif kind == "quick_del_admin":
        items = [u for u in users.admins() if u.user_id != SUPERADMIN_ID]
        title = t("quick_del_admin_title")
    else:
        await call.answer()
        return

    if call.message is None:
        await call.answer()
        return
    await call.message.edit_text(
        title, parse_mode="HTML",
        reply_markup=kb_quick_pick(items, kind, page=page),
    )
    await call.answer()


@router.callback_query(F.data.startswith("quickpick:"))
async def cb_quick_pick(call: CallbackQuery, bot: Bot) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer()
        return
    kind = parts[1]
    try:
        target_id = int(parts[2])
    except ValueError:
        await call.answer(t("id_error"), show_alert=True)
        return

    target = users.get(target_id)
    if target is None:
        await call.answer(t("user_not_found"), show_alert=True)
        return
    if users.is_superadmin(target_id):
        await call.answer(t("cant_touch_super"), show_alert=True)
        return

    if kind == "quick_ban":
        users.ban(target_id)
        try:
            await bot.send_message(target_id, t("notify_banned"))
        except Exception:
            pass
    elif kind == "quick_unban":
        users.unban(target_id)
        try:
            await bot.send_message(target_id, t("notify_unbanned"))
        except Exception:
            pass
    elif kind == "quick_add_admin":
        if not users.is_superadmin(call.from_user.id):
            await call.answer(t("only_superadmin"), show_alert=True)
            return
        users.make_admin(target_id)
        try:
            await bot.send_message(target_id, t("notify_makeadmin"))
        except Exception:
            pass
    elif kind == "quick_del_admin":
        if not users.is_superadmin(call.from_user.id):
            await call.answer(t("only_superadmin"), show_alert=True)
            return
        users.remove_admin(target_id)
        try:
            await bot.send_message(target_id, t("notify_removeadmin"))
        except Exception:
            pass
    else:
        await call.answer()
        return

    if call.message is not None:
        try:
            await call.message.edit_text(
                f"{t('admin_panel_title')}\n\n{t('admin_panel_sub')}",
                parse_mode="HTML",
                reply_markup=kb_admin_panel(is_super=users.is_superadmin(call.from_user.id)),
            )
        except TelegramBadRequest:
            pass
    await call.answer(t("done"))


# ─────────────────────────── Callback: действия с юзером ───────────────────────────

@router.callback_query(F.data.startswith("user:"))
async def cb_user_action(call: CallbackQuery, bot: Bot) -> None:
    if not _is_admin(call.from_user):
        await call.answer(t("no_access"), show_alert=True)
        return
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer()
        return
    action = parts[1]
    try:
        target_id = int(parts[2])
    except ValueError:
        await call.answer(t("id_error"), show_alert=True)
        return

    if users.is_superadmin(target_id) and action in ("ban", "removeadmin", "remove"):
        await call.answer(t("cant_touch_super"), show_alert=True)
        return
    if not users.is_superadmin(call.from_user.id) and action in ("makeadmin", "removeadmin"):
        await call.answer(t("only_superadmin"), show_alert=True)
        return

    target = users.get(target_id)
    if target is None:
        await call.answer(t("user_not_found"), show_alert=True)
        return

    if action == "approve":
        users.approve(target_id)
        try:
            await bot.send_message(target_id, t("notify_approved"))
        except Exception:
            pass
    elif action == "ban":
        users.ban(target_id)
        try:
            await bot.send_message(target_id, t("notify_banned"))
        except Exception:
            pass
    elif action == "unban":
        users.unban(target_id)
        try:
            await bot.send_message(target_id, t("notify_unbanned"))
        except Exception:
            pass
    elif action == "makeadmin":
        users.make_admin(target_id)
        try:
            await bot.send_message(target_id, t("notify_makeadmin"))
        except Exception:
            pass
    elif action == "removeadmin":
        users.remove_admin(target_id)
        try:
            await bot.send_message(target_id, t("notify_removeadmin"))
        except Exception:
            pass
    elif action == "remove":
        users.remove_user(target_id)

    if call.message is not None:
        fresh = users.get(target_id)
        if fresh is None:
            items = [u for u in users.all_users() if u.user_id != SUPERADMIN_ID]
            if not items:
                await call.message.edit_text(
                    t("all_users_empty"), parse_mode="HTML", reply_markup=kb_back_to_users()
                )
            else:
                await call.message.edit_text(
                    t("all_users_title"), parse_mode="HTML",
                    reply_markup=kb_users_list(items, "all", 0),
                )
        else:
            try:
                await call.message.edit_text(
                    _user_card_text(fresh),
                    parse_mode="HTML",
                    reply_markup=kb_user_card(fresh),
                )
            except TelegramBadRequest:
                pass

    await call.answer(t("done"))


# ─────────────────────────── Команды: слова ───────────────────────────

@router.message(Command("words"))
async def cmd_words(message: types.Message) -> None:
    if message.from_user is None or not _is_admin(message.from_user):
        return
    if not settings.bad_words:
        await message.answer(t("words_empty"))
        return
    text = t("words_list") + "\n" + "\n".join(f"• <code>{w}</code>" for w in settings.bad_words)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("addword"))
async def cmd_addword(message: types.Message) -> None:
    if message.from_user is None or not _is_admin(message.from_user):
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer(t("words_usage_add"))
        return
    w = args[1].strip().lower()
    if w and w not in settings.bad_words:
        settings.bad_words.append(w)
        await message.answer(t("words_added").format(w), parse_mode="HTML")
    else:
        await message.answer(t("words_exists"))


@router.message(Command("delword"))
async def cmd_delword(message: types.Message) -> None:
    if message.from_user is None or not _is_admin(message.from_user):
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer(t("words_usage_del"))
        return
    w = args[1].strip().lower()
    if w in settings.bad_words:
        settings.bad_words.remove(w)
        await message.answer(t("words_deleted").format(w), parse_mode="HTML")
    else:
        await message.answer(t("words_not_found"))


# ─────────────────────────── Команды админов ───────────────────────────

@router.message(Command("makeadmin"))
async def cmd_makeadmin(message: types.Message) -> None:
    if message.from_user is None or not users.is_superadmin(message.from_user.id):
        return
    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer(t("cmd_makeadmin_usage"))
        return
    try:
        uid = int(args[1])
    except ValueError:
        await message.answer(t("cmd_id_number"))
        return
    if users.make_admin(uid):
        await message.answer(t("cmd_made_admin").format(uid))
    else:
        await message.answer(t("cmd_user_first_start"))


@router.message(Command("unmakeadmin"))
async def cmd_unmakeadmin(message: types.Message) -> None:
    if message.from_user is None or not users.is_superadmin(message.from_user.id):
        return
    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer(t("cmd_unmakeadmin_usage"))
        return
    try:
        uid = int(args[1])
    except ValueError:
        await message.answer(t("cmd_id_number"))
        return
    if users.remove_admin(uid):
        await message.answer(t("cmd_removed_admin").format(uid))
    else:
        await message.answer(t("user_not_found"))


@router.message(Command("ban"))
async def cmd_ban(message: types.Message) -> None:
    if message.from_user is None or not users.is_admin(message.from_user.id):
        return
    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer(t("cmd_ban_usage"))
        return
    try:
        uid = int(args[1])
    except ValueError:
        await message.answer(t("cmd_id_number"))
        return
    if users.ban(uid):
        await message.answer(t("cmd_banned").format(uid))
    else:
        await message.answer(t("user_not_found"))


@router.message(Command("unban"))
async def cmd_unban(message: types.Message) -> None:
    if message.from_user is None or not users.is_admin(message.from_user.id):
        return
    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer(t("cmd_unban_usage"))
        return
    try:
        uid = int(args[1])
    except ValueError:
        await message.answer(t("cmd_id_number"))
        return
    if users.unban(uid):
        await message.answer(t("cmd_unbanned").format(uid))
    else:
        await message.answer(t("user_not_found"))


@router.message(Command("approve"))
async def cmd_approve(message: types.Message, bot: Bot) -> None:
    if message.from_user is None or not users.is_admin(message.from_user.id):
        return
    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer(t("cmd_approve_usage"))
        return
    try:
        uid = int(args[1])
    except ValueError:
        await message.answer(t("cmd_id_number"))
        return
    if users.approve(uid):
        try:
            await bot.send_message(uid, t("notify_approved"))
        except Exception:
            pass
        await message.answer(t("cmd_approved").format(uid))
    else:
        await message.answer(t("user_not_found"))


# ─────────────────────────── my_chat_member ───────────────────────────

@router.my_chat_member()
async def on_bot_added(event: types.ChatMemberUpdated, bot: Bot) -> None:
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    was_out = old_status in ("left", "kicked")
    now_in = new_status in ("member", "administrator", "restricted")
    chat = event.chat
    added_by = event.from_user

    if was_out and now_in:
        if not settings.enabled and not users.is_superadmin(added_by.id):
            try:
                await bot.leave_chat(chat.id)
            except Exception:
                pass
            return

        allowed = users.has_access(added_by.id)

        if not allowed:
            try:
                await bot.send_message(chat_id=chat.id, text=t("chat_denied_msg"))
            except Exception:
                pass
            try:
                await bot.leave_chat(chat.id)
            except Exception as e:
                log.warning("Не смог покинуть чат %s: %s", chat.id, e)
            if settings.notify_joins:
                try:
                    await bot.send_message(
                        chat_id=added_by.id,
                        text=(
                            f"{t('chat_denied_title')}\n\n"
                            f"{t('chat_name')}: {chat.title or '—'}\n"
                            f"{t('chat_id')}: <code>{chat.id}</code>"
                        ),
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            return

        if chat.type in ("group", "supergroup"):
            known_chats[chat.id] = chat.title or "Без названия"

        if settings.notify_joins:
            try:
                await bot.send_message(
                    chat_id=added_by.id,
                    text=(
                        f"{t('chat_added_title')}\n\n"
                        f"{t('chat_name')}: {chat.title or '—'}\n"
                        f"{t('chat_id')}: <code>{chat.id}</code>"
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                log.warning("Не смог уведомить добавившего: %s", e)

    elif not was_out and new_status in ("left", "kicked"):
        known_chats.pop(chat.id, None)
        if settings.notify_leaves:
            try:
                await bot.send_message(
                    chat_id=added_by.id,
                    text=(
                        f"{t('chat_removed_title')}\n\n"
                        f"{t('chat_name')}: {chat.title or '—'}\n"
                        f"{t('chat_id')}: <code>{chat.id}</code>"
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                log.warning("Не смог уведомить: %s", e)


# ─────────────────────────── /biv ───────────────────────────

@router.message(Command("biv"))
async def biv_command(message: types.Message, bot: Bot) -> None:
    if message.chat.type == "private":
        return

    if not settings.enabled and (message.from_user is None or not users.is_superadmin(message.from_user.id)):
        return

    args = (message.text or "").split()
    if len(args) < 2:
        return

    action = args[1].lower()
    chat_id = message.chat.id

    if action == "start":
        try:
            duration = _parse_duration(args)
            game = manager.begin(chat_id, duration)
        except (InvalidDuration, GameAlreadyRunning) as e:
            await message.answer(f"⚠️ {e}")
            return
        await message.answer(
            f"{t('game_started')}\n"
            f"{t('game_seconds').format(game.duration)}\n"
            f"{t('game_hint')}"
        )
        log.info("Игра запущена в чате %s", chat_id)

    elif action == "stop":
        try:
            await manager.end(bot, chat_id)
        except GameNotRunning as e:
            await message.answer(f"⚠️ {e}")
            return
        await message.answer(t("game_stopped"))

    elif action == "top":
        top = stats.top(chat_id, limit=10)
        if not top:
            await message.answer(t("top_empty"))
            return
        lines = [t("top_title")]
        for i, p in enumerate(top):
            lines.append(f"{_medal(i)} {p.name} — {p.wins} 🏅")
        lines.append("")
        lines.append(f"{t('top_players')}: {stats.total_players(chat_id)}")
        await message.answer("\n".join(lines))

    elif action == "stats":
        user = message.from_user
        if user is None:
            return
        stat = stats.get(chat_id, user.id)
        if stat is None:
            await message.answer(t("my_stats_zero").format(user.username or user.first_name))
            return
        top = stats.top(chat_id, limit=1000)
        place = next((i for i, p in enumerate(top) if p.user_id == user.id), None)
        place_str = f"#{place + 1}" if place is not None else "—"
        await message.answer(
            f"{t('my_stats').format(stat.name)}\n"
            f"{t('my_stats_wins')}: {stat.wins}\n"
            f"{t('my_stats_place')}: {place_str}"
        )

    elif action == "reset":
        stats.reset(chat_id)
        await message.answer(t("reset_done"))


@router.message()
async def on_message(message: types.Message, bot: Bot) -> None:
    if not message.text or message.text.startswith("/"):
        return
    if message.from_user is None:
        return

    if settings.bad_words and settings.is_bad_word(message.text):
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        try:
            await message.answer(t("words_swear").format(message.from_user.full_name))
        except Exception:
            pass
        return

    if not settings.enabled:
        return

    game = manager.get(message.chat.id)
    if not game.active:
        return

    user = message.from_user

    if settings.antiflood and game.leader is not None and game.leader.user_id == user.id:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        return

    leader = Leader(
        user_id=user.id,
        name=user.username or user.first_name,
        text=message.text,
        message_id=message.message_id,
    )
    await game.promote(bot, leader)


# ─────────────────────────── Запуск ───────────────────────────

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )


async def main() -> None:
    setup_logging()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    log.info("Бот запущен. Супер-админ: %s", SUPERADMIN_ID)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        log.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
