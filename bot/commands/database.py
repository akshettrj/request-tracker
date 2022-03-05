from datetime import datetime
from pyrogram import ContinuePropagation
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message

from bot import ( DB, GROUP_ID, HELP_DATA )
from bot.client import app
from bot.filters import CustomFilters
from bot.helpers.utils import (
    is_sudo_user, is_admin, is_owner,
    format_time_diff, html_message_link,
    is_a_request, is_english_request,
    sort_help_data
)


HELP_DATA += [["dropdb", "Drop the whole database ⚠️", ["SUDO", "OWNER"]]]
HELP_DATA += [["dellastreq", "Delete the last request of a user. Reply to message or pass in User ID", ["SUDO", "ADMIN"]]]
HELP_DATA += [["delreq", "Delete a request. Pass in the Message ID", ["SUDO", "ADMIN"]]]
HELP_DATA += [["done", "Mark a request as completed. Reply to the request message", ["SUDO", "ADMIN"]]]
HELP_DATA += [["pending", "Mark a request as not completed. Reply to the request message", ["SUDO", "ADMIN"]]]
sort_help_data()


@app.on_message(filters=CustomFilters.dropdb_cmd_filter)
async def dropdb_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_owner(client, user)):
        raise ContinuePropagation

    DB.drop_database()
    DB.create_schema()

    await message.reply_text(
        text="Successfully dropped database",
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.dellastreq_cmd_filter)
async def dellastreq_cmd(client: Client, message: Message):

    user, body = message.from_user, message.text
    if user is None or body is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    target_user_id = -1
    body_split = body.split("\n")[0].split()

    if len(body_split) >= 2:
        arg = body_split[1]
        if arg.isnumeric():
            target_user_id = int(arg)

    replied_to = message.reply_to_message
    if target_user_id == -1:
        if replied_to is None or replied_to.from_user is None:
            await message.reply_text(
                text='<b>Usages:</b>\n' +
                '1. <code>/dellastreq <user_id></code>\n' +
                '2. Reply <code>/dellastreq</code> to a user\'s message',
                quote=True
            )
            raise ContinuePropagation
        else:
            target_user_id = replied_to.from_user.id

    target_user = None
    try:
        target_user = await client.get_chat_member(GROUP_ID, target_user_id)
    except Exception as _:
        await message.reply_text(
            text="Not a valid id",
            quote=True
        )
        raise ContinuePropagation

    target_user = target_user.user

    user_id = DB.get_user(target_user_id)

    if user_id is None:
        await message.reply_text(
            text='There are no records for the user yet.',
            quote=True
        )
        raise ContinuePropagation

    last_req = DB.get_user_last_request(target_user_id)

    if last_req['user_id'] is None or last_req['message_id'] is None or last_req['req_time'] is None:
        await message.reply_text(
            text='There are no records for the user yet.',
            quote=True
        )
        raise ContinuePropagation

    cur_time = datetime.now()
    group_id = int(str(GROUP_ID)[4:])

    DB.delete_request(last_req['message_id'])

    await message.reply_text(
        text=f'{html_message_link(group_id, last_req["message_id"], "Last request")} of ' +
            f'{target_user.mention(target_user.first_name)} from ' +
            f'{format_time_diff(cur_time, last_req["req_time"])} has been deleted',
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.delreq_cmd_filter)
async def delreq_cmd(client: Client, message: Message):

    user, body = message.from_user, message.text
    if user is None or body is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    target_message_id = -1
    body_split = body.split("\n")[0].split()

    if len(body_split) >= 2:
        arg = body_split[1]
        if arg.isnumeric():
            target_message_id = int(arg)

    replied_to = message.reply_to_message
    if target_message_id == -1:
        if replied_to is None:
            await message.reply_text(
                text='<b>Usages:</b>\n' +
                '1. <code>/delreq <message_id></code>\n' +
                '2. Reply <code>/delreq</code> to a user\'s message',
                quote=True
            )
            raise ContinuePropagation
        else:
            target_message_id = replied_to.message_id

    DB.delete_request(target_message_id)

    await message.reply_text(
        text="The request has been deleted from records",
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.done_cmd_filter)
async def done_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    replied_to = message.reply_to_message
    if (replied_to is None) or (not is_a_request(replied_to)):
        await message.reply(
            text="Please reply to a request message",
            quote=True
        )
        raise ContinuePropagation

    target_user = replied_to.from_user
    if target_user is None:
        await message.reply(
            text="Couldn't find any user in the replied message :panick:",
            quote=True
        )
        raise ContinuePropagation

    user_id = DB.get_user(target_user.id)
    if user_id is None:
        target_user_name = f"{target_user.first_name} {target_user.last_name or ''}".strip()
        DB.add_user(target_user.id, target_user_name, target_user.username or '')
    user_id = target_user.id

    is_english = is_english_request(replied_to)
    if DB.get_request(user_id, replied_to.message_id)[0] is None:
        DB.register_request(user_id, is_english, replied_to.message_id)

    DB.register_request_fulfillment(user_id, replied_to.message_id, message.message_id, user.id)

    group_id = int(str(GROUP_ID)[4:])
    await message.reply_text(
        text=f"{html_message_link(group_id, replied_to.message_id, 'Request')} marked as fulfilled\n",
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.notdone_cmd_filter)
async def notdone_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    replied_to = message.reply_to_message
    if (replied_to is None) or (not is_a_request(replied_to)):
        await message.reply(
            text="Please reply to a request message",
            quote=True
        )
        raise ContinuePropagation

    target_user = replied_to.from_user
    if target_user is None:
        await message.reply(
            text="Couldn't find any user in the replied message :panick:",
            quote=True
        )
        raise ContinuePropagation

    user_id = DB.get_user(target_user.id)
    if user_id is None:
        target_user_name = f"{target_user.first_name} {target_user.last_name or ''}".strip()
        DB.add_user(target_user.id, target_user_name, target_user.username or '')
    user_id = target_user.id

    is_english = is_english_request(replied_to)
    if DB.get_request(user_id, replied_to.message_id)[0] is None:
        DB.register_request(user_id, is_english, replied_to.message_id)

    DB.mark_request_not_done(user_id, replied_to.message_id)

    group_id = int(str(GROUP_ID)[4:])
    await message.reply_text(
        text=f"{html_message_link(group_id, replied_to.message_id, 'Request')} marked as pending\n",
        quote=True
    )

    raise ContinuePropagation
