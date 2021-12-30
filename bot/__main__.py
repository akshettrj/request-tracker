from datetime import datetime
from pyrogram.types.user_and_chats.chat_member import ChatMember
from bot import ( BOT_TOKEN, FULFILL_FILTER, LIMITS_COMMAND_FILTER, REQ_TIMES, REQUEST_FILTER,
        GROUP_ID, API_HASH, API_ID, DATABASE_URL, START_COMMAND_FILTER, STATS_COMMAND_FILTER )

from pyrogram import Client
from pyrogram.types import Message
from bot.helpers.utils import ( format_time_diff, get_message_media, is_a_request,
        is_english_request, html_message_link, time_gap_not_crossed )

from bot.helpers.database import Database

db = Database(DATABASE_URL)

app = Client(
            session_name='req_delete_bot',
            api_hash=API_HASH,
            api_id=API_ID,
            bot_token=BOT_TOKEN,
        )

@app.on_message(filters=FULFILL_FILTER, group=0)
async def request_fulfill_handler(client: Client, message: Message):
    user = message.from_user
    if user is None:
        return

    # membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
    # if membership.status not in ['administrator', 'creator']:
    #     return

    replied_to = message.reply_to_message
    if replied_to is None:
        return

    media = get_message_media(message)
    if media is None:
        return

    if not is_a_request(replied_to):
        return None

    is_english = is_english_request(replied_to)

    user_id = replied_to.from_user.id
    user_data = db.get_user(user_id)
    if user_data[0] is None:
        db.add_user(user_id)

    db.register_request_fulfillment(user_id, is_english, message.message_id)

@app.on_message(filters=REQUEST_FILTER, group=1)
async def request_handler(client: Client, message: Message):
    user = message.from_user
    if user is None:
        return

    membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
    if membership.status in ['administrator', 'creator']:
        return

    if message.text is None:
        return

    if not is_a_request(message):
        return

    is_english = is_english_request(message)

    ( user_id, last_eng_req, last_eng_req_id, last_eng_fulfill,
        last_eng_fulfill_id, last_non_eng_req,
        last_non_eng_req_id, last_non_eng_fulfill,
        last_non_eng_fulfill_id ) = db.get_user(user.id)

    if user_id is None:
        db.add_user(user.id)
        db.register_request(user.id, is_english, message.message_id)
        return

    cur_time = datetime.now()
    group_id = int(str(GROUP_ID)[4:])
    if is_english:
        if last_eng_req is None and last_eng_fulfill is None:
            return
        elif last_eng_req is not None and last_eng_fulfill is None:
            if time_gap_not_crossed(cur_time, last_eng_req, REQ_TIMES['eng']):
                await message.delete()
                await client.send_message(
                    chat_id=GROUP_ID,
                    text=f'{user.mention(user.first_name)}, your '+\
                            f'{html_message_link(group_id, last_eng_req_id, "last request")} '+\
                            f'was less than {REQ_TIMES["eng"]["full"]} ago and hence your new request is deleted.'
                )
                return
        elif last_eng_fulfill is not None and last_eng_req is None:
            if time_gap_not_crossed(cur_time, last_eng_fulfill, REQ_TIMES['eng']):
                await message.delete()
                await client.send_message(
                    chat_id=GROUP_ID,
                    text=f'{user.mention(user.first_name)}, your last request was '+\
                            f'{html_message_link(group_id, last_eng_fulfill_id, "fulfilled")} '+\
                            'was less than {REQ_TIMES["eng"]["full"]} ago and hence your new request is deleted.'
                )
                return
        elif last_eng_fulfill is not None and last_eng_req is not None:
            if last_eng_req > last_eng_fulfill:
                if time_gap_not_crossed(cur_time, last_eng_req, REQ_TIMES['eng']):
                    await message.delete()
                    await client.send_message(
                        chat_id=GROUP_ID,
                        text=f'{user.mention(user.first_name)}, your ' +\
                                f'{html_message_link(group_id, last_eng_req_id, "last request")} ' +\
                                f'was less than {REQ_TIMES["eng"]["full"]} ago and hence your new request is deleted.'
                    )
                    return
            else:
                if time_gap_not_crossed(cur_time, last_eng_fulfill, REQ_TIMES['eng']):
                    await message.delete()
                    await client.send_message(
                        chat_id=GROUP_ID,
                        text=f'{user.mention(user.first_name)}, your last request was '+\
                                f'{html_message_link(group_id, last_eng_fulfill_id, "fulfilled")} '+\
                                f'was less than {REQ_TIMES["eng"]["full"]} ago and hence your new request is deleted.'
                    )
                    return

        db.register_request(user.id, is_english, message.message_id)

    else:
        if last_non_eng_req is None and last_non_eng_fulfill is None:
            return
        elif last_non_eng_req is not None and last_non_eng_fulfill is None:
            if time_gap_not_crossed(cur_time, last_non_eng_req, REQ_TIMES['non_eng']):
                await message.delete()
                await client.send_message(
                    chat_id=GROUP_ID,
                    text=f'{user.mention(user.first_name)}, your '+\
                            f'{html_message_link(group_id, last_non_eng_req_id, "last non-english request")} '+\
                            f'was less than {REQ_TIMES["non_eng"]["full"]} ago and hence your new request is deleted.'
                )
                return
        elif last_non_eng_fulfill is not None and last_non_eng_req is None:
            if time_gap_not_crossed(cur_time, last_non_eng_fulfill, REQ_TIMES['non_eng']):
                await message.delete()
                await client.send_message(
                    chat_id=GROUP_ID,
                    text=f'{user.mention(user.first_name)}, your last non-english request was '+\
                            f'{html_message_link(group_id, last_non_eng_fulfill_id, "fulfilled")} '+\
                            f'was less than {REQ_TIMES["non_eng"]["full"]} ago and hence your new request is deleted.'
                )
                return
        elif last_non_eng_fulfill is not None and last_non_eng_req is not None:
            if last_non_eng_req > last_non_eng_fulfill:
                if time_gap_not_crossed(cur_time, last_non_eng_req, REQ_TIMES['non_eng']):
                    await message.delete()
                    await client.send_message(
                        chat_id=GROUP_ID,
                        text=f'{user.mention(user.first_name)}, your ' +\
                                f'{html_message_link(group_id, last_non_eng_req_id, "last non-english request")} ' +\
                                f'was less than {REQ_TIMES["non_eng"]["full"]} ago and hence your new request is deleted.'
                    )
                    return
            else:
                if time_gap_not_crossed(cur_time, last_non_eng_fulfill, REQ_TIMES['non_eng']):
                    await message.delete()
                    await client.send_message(
                        chat_id=GROUP_ID,
                        text=f'{user.mention(user.first_name)}, your last non-english request was '+\
                                f'{html_message_link(group_id, last_non_eng_fulfill_id, "fulfilled")} '+\
                                f'was less than {REQ_TIMES["non_eng"]["full"]} ago and hence your new request is deleted.'
                    )
                    return

        db.register_request(user.id, is_english, message.message_id)


@app.on_message(filters=STATS_COMMAND_FILTER, group=2)
async def get_user_data(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
    if membership.status not in ['administrator', 'creator']:
        return

    body = message.text
    if body is None:
        return

    target_user_id = -1

    body_split = body.split("\n")[0].split()

    if len(body_split) >= 2:
        arg = body_split[1]
        if arg.isnumeric():
            target_user_id = int(arg)

    replied_to = message.reply_to_message
    if target_user_id == -1:
        if replied_to is None:
            await message.reply_text(
                text='<b>Usages:</b>\n' +
                '1. <code>/stats <user_id></code>\n' +
                '2. Reply <code>/stats</code> to a user\'s message',
                quote=True
            )
            return
        else:
            target_user_id = replied_to.from_user.id


    ( user_id, last_eng_req, last_eng_req_id, last_eng_fulfill,
        last_eng_fulfill_id, last_non_eng_req,
        last_non_eng_req_id, last_non_eng_fulfill,
        last_non_eng_fulfill_id ) = db.get_user(target_user_id)

    if user_id is None:
        await message.reply_text(
            text='There are no records for the user yet.',
            quote=True
        )
        return

    curr_time = datetime.now()
    group_id = int(str(GROUP_ID)[4:])

    p_last_eng_req = "Not found"
    p_last_eng_fulfill = "Not found"
    p_last_non_eng_req = "Not found"
    p_last_non_eng_fulfill = "Not found"

    if last_eng_req is not None and last_eng_req_id is not None:
        p_last_eng_req = f"<code>{format_time_diff(curr_time, last_eng_req)}</code> → {html_message_link(group_id, last_eng_req_id, 'link')}"

    if last_eng_fulfill is not None and last_eng_fulfill_id is not None:
        p_last_eng_fulfill = f"<code>{format_time_diff(curr_time, last_eng_fulfill)}</code> → {html_message_link(group_id, last_eng_fulfill_id, 'link')}"

    if last_non_eng_req is not None and last_non_eng_req_id is not None:
        p_last_non_eng_req = f"<code>{format_time_diff(curr_time, last_non_eng_req)}</code> → {html_message_link(group_id, last_non_eng_req_id, 'link')}"

    if last_non_eng_fulfill is not None and last_non_eng_fulfill_id is not None:
        p_last_non_eng_fulfill = f"<code>{format_time_diff(curr_time, last_non_eng_fulfill)}</code> → {html_message_link(group_id, last_non_eng_fulfill_id, 'link')}"

    stats_message = f"<b>Stats for</b> <code>{user_id}</code>:\n\n" + \
                    f"<u>Eng Request</u>: {p_last_eng_req}\n" + \
                    f"<u>Eng Fulfilled</u>: {p_last_eng_fulfill}\n" + \
                    f"<u>Non-Eng Request</u>: {p_last_non_eng_req}\n" + \
                    f"<u>Non-Eng Fulfilled</u>: {p_last_non_eng_fulfill}\n"

    await message.reply_text(
                text=stats_message,
                quote=True
            )

@app.on_message(filters=START_COMMAND_FILTER, group=3)
async def start_command(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
    if membership.status not in ['administrator', 'creator']:
        return

    await message.reply_text(
        text="Hi I am up and tracking the requests 😎",
        quote=True
    )

@app.on_message(filters=LIMITS_COMMAND_FILTER, group=4)
async def limits_command(client: Client, message: Message):

    limits_message = f'<b>These are the current limits</b>:\n\n' + \
                    f'<u>Eng. Requests</u>: {REQ_TIMES["eng"]["value"]}{REQ_TIMES["eng"]["type"]}\n' + \
                    f'<u>Non-Eng. Requests</u>: {REQ_TIMES["non_eng"]["value"]}{REQ_TIMES["non_eng"]["type"]}'

    await message.reply_text(
        text=limits_message,
        quote=True
    )

app.run()
