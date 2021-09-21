from functools import wraps
from cachetools import TTLCache
from threading import RLock
from SaitamaRobot import (DEL_CMDS, DEV_USERS, DRAGONS, SUPPORT_CHAT, DEMONS,
                          TIGERS, WOLVES, dispatcher)

from telegram import Chat, ChatMember, ParseMode, Update
from telegram.ext import CallbackContext

# stores admemes in memory for 10 min.
ADMIN_CACHE = TTLCache(maxsize=512, ttl=60 * 10)
THREAD_LOCK = RLock()


def is_whitelist_plus(chat: Chat,
                      user_id: int,
                      member: ChatMember = None) -> bool:
    return any(user_id in user
               for user in [WOLVES, TIGERS, DEMONS, DRAGONS, DEV_USERS])


def is_support_plus(chat: Chat,
                    user_id: int,
                    member: ChatMember = None) -> bool:
    return user_id in DEMONS or user_id in DRAGONS or user_id in DEV_USERS


def is_sudo_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in DRAGONS or user_id in DEV_USERS


def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if (chat.type == 'private' or user_id in DRAGONS or user_id in DEV_USERS or
            chat.all_members_are_administrators or
            user_id in [777000, 1087968824
                       ]):  # Count telegram and Group Anonymous as admin
        return True

    if not member:
        with THREAD_LOCK:
            # try to fetch from cache first.
            try:
                return user_id in ADMIN_CACHE[chat.id]
            except BaseException:
                # keyerror happend means cache is deleted,
                # so query bot api again and return user status
                # while saving it in cache for future useage...
                chat_admins = dispatcher.bot.getChatAdministrators(chat.id)
                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list

                if user_id in admin_list:
                    return True
                return False


def is_bot_admin(chat: Chat,
                 bot_id: int,
                 bot_member: ChatMember = None) -> bool:
    if chat.type == 'private' or chat.all_members_are_administrators:
        return True

    if not bot_member:
        bot_member = chat.get_member(bot_id)

    return bot_member.status in ('administrator', 'creator')


def can_delete(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_delete_messages


def is_user_ban_protected(chat: Chat,
                          user_id: int,
                          member: ChatMember = None) -> bool:
    if (chat.type == 'private' or user_id in DRAGONS or user_id in DEV_USERS or
            user_id in WOLVES or user_id in TIGERS or
            chat.all_members_are_administrators or
            user_id in [777000, 1087968824
                       ]):  # Count telegram and Group Anonymous as admin
        return True

    if not member:
        member = chat.get_member(user_id)

    return member.status in ('administrator', 'creator')


def is_user_in_chat(chat: Chat, user_id: int) -> bool:
    member = chat.get_member(user_id)
    return member.status not in ('left', 'kicked')


def dev_plus(func):

    @wraps(func)
    def is_dev_plus_func(update: Update, context: CallbackContext, *args,
                         **kwargs):
        bot = context.bot
        user = update.effective_user

        if user.id in DEV_USERS:
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()
        else:
            update.effective_message.reply_text(
                "Bu əmri istifadə etmək hüququna sahib deyilsən")

    return is_dev_plus_func


def sudo_plus(func):

    @wraps(func)
    def is_sudo_plus_func(update: Update, context: CallbackContext, *args,
                          **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_sudo_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()
        else:
            update.effective_message.reply_text(
                "Admin olmayan biri mənə nə etməli olduğumu deyir? Deyəsən döyülmək istəyirsən!")

    return is_sudo_plus_func


def support_plus(func):

    @wraps(func)
    def is_support_plus_func(update: Update, context: CallbackContext, *args,
                             **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_support_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_support_plus_func


def whitelist_plus(func):

    @wraps(func)
    def is_whitelist_plus_func(update: Update, context: CallbackContext, *args,
                               **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_whitelist_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                f"Bunu etmək hüququn yoxdur.\n@{SUPPORT_CHAT} -a get")

    return is_whitelist_plus_func


def user_admin(func):

    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()
        else:
            update.effective_message.reply_text(
                "Admin olmayan biri mənə nə etməli olduğumu deyir? Deyəsən döyülmək istəyirsən!")

    return is_admin


def user_admin_no_reply(func):

    @wraps(func)
    def is_not_admin_no_reply(update: Update, context: CallbackContext, *args,
                              **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_not_admin_no_reply


def user_not_admin(func):

    @wraps(func)
    def is_not_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and not is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass

    return is_not_admin


def bot_admin(func):

    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            not_admin = "Admin deyiləm!"
        else:
            not_admin = f"<b>{update_chat_title}</b> qrupunda admin deyiləm!"

        if is_bot_admin(chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                not_admin, parse_mode=ParseMode.HTML)

    return is_admin


def bot_can_delete(func):

    @wraps(func)
    def delete_rights(update: Update, context: CallbackContext, *args,
                      **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_delete = "Burada mesaj silmə səlahiyyətim yoxdur!\nAdmin olduğumdan və mesajları silə bildiyimdən əmin ol."
        else:
            cant_delete = f"<b>{update_chat_title}</b> qrupunda mesajları silə bilmirəm!\nOrada admin olduğumdan və mesajları silə bildiyimdən əmin ol."

        if can_delete(chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_delete, parse_mode=ParseMode.HTML)

    return delete_rights


def can_pin(func):

    @wraps(func)
    def pin_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_pin = "Burada mesaj sabitləyə bilmirəm!\nAdmin olduğumdan və mesaj sabitləyə bildiyimdən əmin ol."
        else:
            cant_pin = f"<b>{update_chat_title}</b> qrupunda mesaj sabitləyə bilmirəm!\nOrada admin olduğumdan və mesaj sabitləyə bildiyimdən əmin ol."

        if chat.get_member(bot.id).can_pin_messages:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_pin, parse_mode=ParseMode.HTML)

    return pin_rights


def can_promote(func):

    @wraps(func)
    def promote_rights(update: Update, context: CallbackContext, *args,
                       **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_promote = "İstifadəçiləri admin edə bilmirəm!\nYeni adminlər təyin edə bildiyimdən əmin ol."
        else:
            cant_promote = (
                f"<b>{update_chat_title}</b> qrupunda istifadəçiləri admin edə bilmirəm!\n"
                f"Orada admin olduğumdan və yeni adminlər təyin edə bildiyimdən əmin ol.")

        if chat.get_member(bot.id).can_promote_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_promote, parse_mode=ParseMode.HTML)

    return promote_rights


def can_restrict(func):

    @wraps(func)
    def restrict_rights(update: Update, context: CallbackContext, *args,
                        **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_restrict = "Burada istifadəçiləri məhdudlaşdıra bilmirəm!\nAdmin olduğumdan və istifadəçiləri məhdudlaşdıra bildiyimdən əmin ol."
        else:
            cant_restrict = f"<b>{update_chat_title}</b> qrupunda istifadəçiləri məhdudlaşdıra bilmirəm!\nAdmin olduğumdan və istifadəçiləri məhdudlaşdıra bildiyimdən əmin ol."

        if chat.get_member(bot.id).can_restrict_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_restrict, parse_mode=ParseMode.HTML)

    return restrict_rights


def user_can_ban(func):

    @wraps(func)
    def user_is_banhammer(update: Update, context: CallbackContext, *args,
                          **kwargs):
        bot = context.bot
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)
        if not (member.can_restrict_members or member.status == "creator"
               ) and not user in DRAGONS and user not in [777000, 1087968824]:
            update.effective_message.reply_text(
                "Bağışla. Sən məni işlətməyə layiq deyilsən.")
            return ""
        return func(update, context, *args, **kwargs)

    return user_is_banhammer


def connection_status(func):

    @wraps(func)
    def connected_status(update: Update, context: CallbackContext, *args,
                         **kwargs):
        conn = connected(
            context.bot,
            update,
            update.effective_chat,
            update.effective_user.id,
            need_admin=False)

        if conn:
            chat = dispatcher.bot.getChat(conn)
            update.__setattr__("_effective_chat", chat)
            return func(update, context, *args, **kwargs)
        else:
            if update.effective_message.chat.type == "private":
                update.effective_message.reply_text(
                    "Hər hansısa qrupda /connect yaz."
                )
                return connected_status

            return func(update, context, *args, **kwargs)

    return connected_status


# Workaround for circular import with connection.py
from SaitamaRobot.modules import connection

connected = connection.connected
