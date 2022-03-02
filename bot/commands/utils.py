from datetime import datetime

from pyrogram import ContinuePropagation
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message

from bot import ( DB, GROUP_ID, HELP_DATA, NAME_CACHE )
from bot.client import app
from bot.filters import CustomFilters
from bot.helpers.utils import (
    is_sudo_user, is_admin, is_owner,
    html_message_link, sort_help_data,
    format_time_diff
)


HELP_DATA += [["pending", "Get all the current pending requests", ["SUDO", "ADMIN"]]]
HELP_DATA += [["lastfilled", "Get the most recently fulfilled request", ["SUDO", "ADMIN"]]]
HELP_DATA += [["schemas", "Get the current table schemas in the database", ["SUDO", "OWNER"]]]
HELP_DATA += [["sqlquery", "Run a SQL query on the dataset. Pass in the query or reply to one", ["SUDO", "OWNER"]]]
HELP_DATA += [["sqlqueryop", "Run a SQL query on the dataset that has some output. Pass in the query or reply to one", ["SUDO", "OWNER"]]]
sort_help_data()


@app.on_message(filters=CustomFilters.pending_cmd_filter)
async def pending_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    pending_requests = DB.get_pending_requests()

    if len(pending_requests) == 0:
        await message.reply_text(
            text="There are no pending requests in records :)",
            quote=True
        )
        raise ContinuePropagation

    pending_req_text = f'Here are the oldest pending requests:\n\n'

    group_id = int(str(GROUP_ID)[4:])
    cur_time = datetime.now()

    for indx,request in enumerate(pending_requests):

        pending_req_text += f'{indx+1}. {html_message_link(group_id, request["message_id"], f"Request {indx+1}")}, '
        pending_req_text += f'<i>{format_time_diff(cur_time, request["req_time"])}</i> {"#English" if request["is_english"] else "#NonEnglish"} '
        pending_req_text += f'(<code>/delreq {request["message_id"]}</code>)\n'

    await message.reply_text(
        text=pending_req_text,
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.lastfilled_cmd_filter)
async def lastfilled_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    last_filled_req = DB.get_latest_fulfilled()
    if (
        last_filled_req['user_id'] is None or last_filled_req['message_id'] is None
        or last_filled_req['req_time'] is None or last_filled_req['fulfill_message_id'] is None
        or last_filled_req['fulfill_time'] is None
    ):
        await message.reply_text(
            text="No request has been fulfilled till now 😢",
            quote=True
        )
        raise ContinuePropagation

    group_id = int(str(GROUP_ID)[4:])
    cur_time = datetime.now()

    reply_text = "<b>The latest fulfilled request was:</b>\n\n"
    reply_text += f"- <b>Type:</b> {'English' if last_filled_req['is_english'] else 'Non English'}\n\n"
    reply_text += f"- {html_message_link(group_id, last_filled_req['message_id'], 'Request')} was {format_time_diff(cur_time, last_filled_req['req_time'])}\n"
    reply_text += f"- {html_message_link(group_id, last_filled_req['fulfill_message_id'], 'Fulfilled')} was {format_time_diff(cur_time, last_filled_req['fulfill_time'])}"

    fulfilled_by_id = last_filled_req['fulfilled_by']
    if fulfilled_by_id is not None and fulfilled_by_id in NAME_CACHE.keys():
        reply_text += f' by <a href="tg://user?id={fulfilled_by_id}">{NAME_CACHE[fulfilled_by_id]["name"]}</a>'

    await message.reply_text(
        text=reply_text,
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.sqlquery_cmd_filter)
async def sqlquery_cmd(client: Client, message: Message):

    user, body, replied_to = (
        message.from_user, message.text, message.reply_to_message
    )
    if user is None or body is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_owner(client, user)):
        raise ContinuePropagation

    sql_query = None
    body_split = body.split(maxsplit=1)

    if len(body_split) > 1:
        sql_query = body_split[1]

    elif replied_to is not None:
        sql_query = replied_to.text

    if sql_query is None:
        await message.reply_text(
            text=(
                "No SQL query found.\n\nUsage:\n"
                "- <code>/sqlquery <QUERY_HERE></code>\n"
                "- <code>reply /sqlquery to message containing SQL_QUERY</code>"
            ),
            quote=True
        )
        raise ContinuePropagation

    try:
        output = DB.run_qeury(sql_query, True if "sqlqueryop" in body else False)
    except Exception as ex:
        await message.reply_text(
            text=f"Error occurred while execution:\n\n<code>{ex}</code>",
            quote=True
        )
        raise ContinuePropagation

    await message.reply_text(
        text=(
            "Successfully executed!\nOutput:\n\n"
            f"<code>{output}</code>"
        ),
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.schemas_cmd_filter)
async def schemas_cmd(client: Client, message: Message):

    user = message.from_user

    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_owner(client, user)):
        raise ContinuePropagation

    try:
        output = DB.get_schemas()
    except Exception as ex:
        await message.reply_text(
            text=f"Error occurred while execution:\n\n<code>{ex}</code>",
            quote=True
        )
        raise ContinuePropagation

    await message.reply_text(
        text=(
            "Schema for <code>users</code>:\n"
            f"<code>{output[0]}</code>\n\n"
            "Schema for <code>requests</code>:\n"
            f"<code>{output[1]}</code>\n\n"
        ),
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.formfulfilled_cmd_filter)
async def formfulfilled_cmd(client: Client, message: Message):

    user = message.from_user

    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_owner(client, user)):
        raise ContinuePropagation

    all_requests = DB.get_requests()

    group_id = int(str(GROUP_ID)[4:])

    errors_message = "ERRORS:\n\n"
    success_message = "SUCCESSES:\n\n"

    for request in all_requests:

        try:
            fulfill_message = await client.get_messages(
                                    chat_id=GROUP_ID,
                                    message_ids=request['fulfill_message_id']
                                )
        except:
            fulfill_message = None

        if fulfill_message is None:
            errors_message += f"{html_message_link(group_id, request['fulfill_message_id'], 'nfmsg')} - {html_message_link(group_id, request['message_id'], 'Request')}\n"
            continue

        fulfiller = fulfill_message.from_user
        if fulfiller is None:
            errors_message += f"{html_message_link(group_id, request['fulfill_message_id'], 'nfmsg')} - {html_message_link(group_id, request['message_id'], 'Request')} - unf\n"
            continue

        DB.update_fulfilled_by(fulfill_message.message_id, fulfiller.id)
        success_message += f"{html_message_link(group_id, request['message_id'], 'Request')} - {html_message_link(group_id, request['fulfill_message_id'], 'fulfilled')} - {fulfiller.mention(fulfiller.first_name)}\n"

    await message.reply_text(
        text=errors_message,
        quote=True
    )
    await message.reply_text(
        text=success_message,
        quote=True
    )
