from pyrogram import filters
from pyrogram.types.messages_and_media.message import Message
from bot import ( COMMAND_PREFIXES, EZBOOKBOT_ID, GROUP_ID, SUDO_USERS )

async def _is_ezbook_bot_message(_, __, update: Message):

    user = update.from_user
    if user is None:
        return False

    return user.id == EZBOOKBOT_ID

async def _is_sudo_user(_, __, update: Message):

    user = update.from_user
    if user is None:
        return False

    return user.id in SUDO_USERS

_ezbook_bot_filter = filters.create(_is_ezbook_bot_message)
_sudo_user_filter = filters.create(_is_sudo_user)
_main_group_filter = filters.chat(GROUP_ID)


class CustomFilters:

    request_filter = (
        ~filters.edited
        & filters.text
        & _main_group_filter
    )

    fulfill_filter = (
        ~filters.edited
        & _main_group_filter
        & (filters.audio | filters.voice | filters.document | _ezbook_bot_filter)
    )

    start_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("start", COMMAND_PREFIXES)
    )

    help_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("help", COMMAND_PREFIXES)
    )

    limits_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("limits", COMMAND_PREFIXES)
    )

    dropdb_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("dropdb", COMMAND_PREFIXES)
    )

    dellastreq_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("dellastreq", COMMAND_PREFIXES)
    )

    delreq_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("delreq", COMMAND_PREFIXES)
    )

    done_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("done", COMMAND_PREFIXES)
    )

    notdone_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("notdone", COMMAND_PREFIXES)
    )

    requests_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("requests", COMMAND_PREFIXES)
    )

    stats_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("stats", COMMAND_PREFIXES)
    )

    pending_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("pending", COMMAND_PREFIXES)
    )

    lastfilled_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("lastfilled", COMMAND_PREFIXES)
    )

    sqlquery_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command(["sqlquery", "sqlqueryop"], COMMAND_PREFIXES)
    )

    schemas_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("schemas", COMMAND_PREFIXES)
    )

    formfulfilled_cmd_filter = (
        ~filters.edited
        & (_sudo_user_filter | _main_group_filter)
        & filters.command("formfulfilled", COMMAND_PREFIXES)
    )
