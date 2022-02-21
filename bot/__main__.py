from datetime import datetime
from pytz import timezone
import os
from time import sleep
from typing import List

from pyrogram import ContinuePropagation
from pyrogram.client import Client
from pyrogram.types import Message

from bot.client import app
from bot import (
    DB, DB_BACKUP_CHAT_ID, GROUP_ID, HELP_DATA,
    EZBOOKBOT_ID, NAME_CACHE, REQ_TIMES
)
from bot.filters import CustomFilters
from bot.helpers.utils import (
    is_sudo_user, is_admin, get_message_media, has_link,
    is_a_request, is_english_request, html_message_link,
    check_time_gap_crossed, sort_help_data, format_time_diff
)

# ⚠️ DON'T REMOVE THIS LINE, THESE ARE MODULES FOR THE BOT ⚠️
from bot.commands import stats, database, utils
from bot.helpers.utils.telegram import mute_user

from apscheduler.schedulers.background import BackgroundScheduler

@app.on_message(filters=CustomFilters.fulfill_filter)
async def request_fulfill_handler(client: Client, message: Message):

    user, replied_to = message.from_user, message.reply_to_message
    if user is None or replied_to is None:
        raise ContinuePropagation

    if user.id == EZBOOKBOT_ID:

        if replied_to is None:
            await message.delete(revoke=True)
            raise ContinuePropagation

        else:
            user_id = replied_to.from_user.id
            db_request = DB.get_request(user_id, replied_to.message_id)
            if db_request[0] is None:
                await message.delete(revoke=True)
                raise ContinuePropagation


    if replied_to is None:
        raise ContinuePropagation

    if user.id != EZBOOKBOT_ID and get_message_media(message) is None:
        raise ContinuePropagation

    if not is_a_request(replied_to):
        raise ContinuePropagation

    is_english = is_english_request(replied_to)

    user_id = replied_to.from_user.id
    user_data = DB.get_user(user_id)

    if user_data is None:
        user_name = f"{replied_to.from_user.first_name} {replied_to.from_user.last_name or ''}".strip()
        DB.add_user(user_id, user_name, replied_to.from_user.username or '')

    if DB.get_request(user_id, replied_to.message_id)[0] is None:
        DB.register_request(user_id, is_english, replied_to.message_id)
        await client.send_reaction(
            chat_id=message.chat.id,
            message_id=replied_to.message_id,
            emoji="🔥"
        )

    DB.register_request_fulfillment(user_id, replied_to.message_id, message.message_id, user.id)
    await client.send_reaction(
        chat_id=message.chat.id,
        message_id=replied_to.message_id,
        emoji="🔥"
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.request_filter)
async def request_handler(client: Client, message: Message):

    user, body = message.from_user, message.text
    if user is None or body is None:
        raise ContinuePropagation

    if (await is_sudo_user(user)) or (await is_admin(client, user)):
        raise ContinuePropagation

    if not is_a_request(message):
        if ("#request" in body.lower()) and ("#audiobook" not in body.lower()):
            await message.reply_text(
                text="/warn This is an exclusive audiobook only group, no ebook requests allowed read the rules.",
                quote=True
            )
            sleep(1)
            await message.delete()
        raise ContinuePropagation

    is_english = is_english_request(message)

    if message.via_bot is None:

        request_lines = body.split("\n")
        request_lines = [
            line.strip()
            for line in request_lines
            if line.strip() != ''
        ]

        if len(request_lines) != 5 or (not has_link(message)):

            await message.delete()
            await client.send_message(
                chat_id=GROUP_ID,
                text=(f"{user.mention(user.first_name)}, "
                   "Make sure your request is in correct format:\n\n"
                   "<i>#request #audiobook (+ other needed tags)</i>\n"
                   "<i>Title</i>\n"
                   "<i>Author</i>\n"
                   "<i>Publisher (or Self-published when publisher isn't specified)</i>\n"
                   "<i>Link</i>\n\n"
                   "- <b>Send a new request in proper format.</b>\n"
                   '- See the <a href="https://t.me/c/1559332818/6059">pinned message</a> for help regarding request generator bot\n'),
            )
            raise ContinuePropagation

    if DB.get_user(user.id) is None:
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        DB.add_user(user.id, user_name, user.username or '')
        DB.register_request(user.id, is_english, message.message_id)
        await client.send_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            emoji="👍"
        )
        raise ContinuePropagation

    cur_time = datetime.now()
    group_id = int(str(GROUP_ID)[4:])

    user_last_request = DB.get_user_last_request(user.id)
    if user_last_request['user_id'] is None:
        DB.register_request(user.id, is_english, message.message_id)
        await client.send_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            emoji="👍"
        )
        raise ContinuePropagation

    req_time = REQ_TIMES['eng'] if user_last_request['is_english'] else REQ_TIMES['non_eng']
    last_req_str = 'English request' if user_last_request['is_english'] else 'Non-English request'

    allow_request = True

    if user_last_request['fulfill_message_id'] is None:
        crossed, appr_time = check_time_gap_crossed(cur_time, user_last_request['req_time'], req_time)
        time_diff = appr_time - cur_time
        if not crossed:
            await client.send_message(
                chat_id=GROUP_ID,
                text=f"{user.mention(user.first_name)}, your " +\
                        f"last {html_message_link(group_id, user_last_request['message_id'], last_req_str)} " +\
                        f"({format_time_diff(cur_time, user_last_request['req_time'])}) " +\
                        f"was less than {req_time['full']} ago and hence the new one is deleted." +\
                        f"\n\nMuting you for 12 hours." +\
                        f"\nCome back after {format_time_diff(t1=None, t2=None, t_diff=time_diff).replace(' ago', '')} (on {appr_time.replace(tzinfo=timezone('Asia/Kolkata')):%d %b} IST)"
            )
            allow_request = False

    else:
        crossed, appr_time = check_time_gap_crossed(cur_time, user_last_request['fulfill_time'], req_time)
        time_diff = appr_time - cur_time
        if not crossed:
            await client.send_message(
                chat_id=GROUP_ID,
                text=f"{user.mention(user.first_name)}, your " + \
                        f"last {html_message_link(group_id, user_last_request['message_id'], last_req_str)} " +\
                        f"({format_time_diff(cur_time, user_last_request['req_time'])}) " +\
                        f"was {html_message_link(group_id, user_last_request['fulfill_message_id'], 'fulfilled')} " +\
                        f"({format_time_diff(cur_time, user_last_request['fulfill_time'])}) " +\
                        f"less than {req_time['full']} ago and hence the new one is deleted." +\
                        f"\n\nMuting you for 12 hours." +\
                        f"\nCome back after {format_time_diff(t1=None, t2=None, t_diff=time_diff).replace(' ago', '')} (on {appr_time.replace(tzinfo=timezone('Asia/Kolkata')):%d %b} IST)"
            )
            allow_request = False

    if not allow_request:

        sleep(1)

        # Delete replies from EZBOOK BOT
        try:
            replies = await client.get_messages(
                chat_id=GROUP_ID,
                reply_to_message_ids=message.message_id
            )
            if isinstance(replies, Message):
                if replies.from_user and replies.from_user.id == EZBOOKBOT_ID:
                    await replies.delete()
                    await client.send_message(
                        chat_id=GROUP_ID,
                        text="⚠️  There was a reply from EZ Book Bot and so user might have got his request fulfilled."
                    )
            elif isinstance(replies, List):
                for reply in replies:
                    if reply.from_user and reply.from_user.id == EZBOOKBOT_ID:
                        await reply.delete()
                        await client.send_message(
                            chat_id=GROUP_ID,
                            text="⚠️  There was a reply from EZ Book Bot and so user might have got his request fulfilled."
                        )
        except:
            pass

        await mute_user(client, user)
        await message.delete()
        raise ContinuePropagation

    DB.register_request(user.id, is_english, message.message_id)
    await client.send_reaction(
        chat_id=message.chat.id,
        message_id=message.message_id,
        emoji="👍"
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.help_cmd_filter)
async def help_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client ,user)):
        raise ContinuePropagation

    sort_help_data()

    help_message = "<u>Commands:</u>\n\n"
    for help in HELP_DATA:
        help_message += f"- <code>/{help[0]}</code> : {help[1]} ({' + '.join(help[2])})\n"

    await message.reply_text(
        text=help_message,
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.userdetails_updater_filter, group=-1)
def update_user_details(_: Client, message: Message):

    global NAME_CACHE
    user = message.from_user
    if user is None:
        raise ContinuePropagation

    name = f"{user.first_name} {user.last_name or ''}".strip()
    username = user.username or ''
    cached_details = NAME_CACHE[user.id] if user.id in NAME_CACHE.keys() else None
    user_data = DB.get_user(user.id)

    if user_data is None or cached_details is None:
        try:
            DB.add_user(user.id, name, username)
            NAME_CACHE[user.id] = {"name": name, "user_name": username}
        except:
            pass
        raise ContinuePropagation

    if name != cached_details['name'] or username != cached_details['user_name']:
        try:
            DB.update_user(user.id, name, username)
            NAME_CACHE[user.id] = {"name": name, "user_name": username}
        except:
            pass

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.backupdb_cmd_filter)
async def pending_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    create_backup()

    raise ContinuePropagation


def create_backup():

    try:
        zip_file_name = DB.get_backup_data()
        _ = app.send_document(
            chat_id=DB_BACKUP_CHAT_ID,
            document=zip_file_name,
            caption="#database #backup"
        )
        os.remove(zip_file_name)

    except Exception as ex:
        _ = app.send_message(
            chat_id=DB_BACKUP_CHAT_ID,
            text=f"Failed to take backup:\n\n <code>{ex}</code>"
        )


if DB_BACKUP_CHAT_ID != -1:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=create_backup,
        trigger="interval",
        seconds=20*60*60,       # 20 Hrs
        max_instances=1
    )
    scheduler.start()

app.run()
