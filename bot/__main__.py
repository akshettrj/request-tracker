from datetime import datetime
from pyrogram.types.user_and_chats.chat_member import ChatMember
from bot import ( BOT_TOKEN, CLEAR_LAST_REQUEST_COMMAND_FILTER, DONE_COMMAND_FILTER, EZBOOKBOT_ID, GROUP_NAME, HELP_COMMAND_FILTER, PENDING_COMMAND_FILTER,
        SESSION_STRING, LIMITS_COMMAND_FILTER, REQ_TIMES, REQUEST_FILTER,
        GROUP_ID, API_HASH, API_ID, DATABASE_URL, START_COMMAND_FILTER,
        REQUESTS_COMMAND_FILTER, STATS_COMMAND_FILTER, DROP_DB_COMMAND_FILTER, FULFILL_FILTER, SUDO_USERS, logger )

from pyrogram import Client
from pyrogram.types import Message
from bot.helpers.utils import ( format_time_diff, get_message_media, is_a_request,
        is_english_request, html_message_link, time_gap_not_crossed )

from bot.helpers.database import Database

db = Database(DATABASE_URL)

app = None
if SESSION_STRING != '':
    app = Client(
                SESSION_STRING,
                api_hash=API_HASH,
                api_id=API_ID,
            )
    logger.info("Logging in using SESSION_STRING")
else:
    app = Client(
                session_name='req_delete_bot',
                api_hash=API_HASH,
                api_id=API_ID,
                bot_token=BOT_TOKEN,
            )
    logger.info("Logging in using BOT_TOKEN")

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

    if user.id != EZBOOKBOT_ID:

        media = get_message_media(message)
        if media is None:
            return

    if not is_a_request(replied_to):
        return None

    is_english = is_english_request(replied_to)

    user_id = replied_to.from_user.id
    user_data = db.get_user(user_id)

    if user_data is None:
        db.add_user(user_id)

    if db.get_request(user_id, replied_to.message_id)[0] is None:
        db.register_request(user_id, is_english, replied_to.message_id)

    db.register_request_fulfillment(user_id, replied_to.message_id, message.message_id)


@app.on_message(filters=REQUEST_FILTER, group=2)
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

    user_id = db.get_user(user.id)

    if user_id is None:
        db.add_user(user.id)
        db.register_request(user.id, is_english, message.message_id)
        return

    cur_time = datetime.now()
    group_id = int(str(GROUP_ID)[4:])

    user_requests = db.get_user_requests(user.id)

    if len(user_requests) == 0:
        db.register_request(user.id, is_english, message.message_id)
        return

    def get_req_time(req):
        return req['req_time']

    req_by_req_time = sorted(user_requests, key=get_req_time)

    last_req = req_by_req_time[-1]
    req_time = REQ_TIMES['eng'] if last_req['is_english'] else REQ_TIMES['non_eng']
    last_req_str = 'last English request' if last_req['is_english'] else 'last Non-English request'

    if last_req['fulfill_message_id'] is None:
        if time_gap_not_crossed(cur_time, last_req['req_time'], req_time):
            await message.delete()
            await client.send_message(
                chat_id=GROUP_ID,
                text=f"{user.mention(user.first_name)}, your " +\
                        f"{html_message_link(group_id, last_req['message_id'], last_req_str)} " +\
                        f"was less than {req_time['full']} ago and hence is deleted."
            )
            return

    else:
        if time_gap_not_crossed(cur_time, last_req['fulfill_time'], req_time):
            await message.delete()
            await client.send_message(
                chat_id=GROUP_ID,
                text=f"{user.mention(user.first_name)}, your {last_req_str} " +\
                        f"{html_message_link(group_id, last_req['fulfill_message_id'], 'was fulfilled')} " +\
                        f"less than {req_time['full']} ago and hence is deleted."
            )
            return

    db.register_request(user.id, is_english, message.message_id)

@app.on_message(filters=REQUESTS_COMMAND_FILTER, group=3)
async def get_user_data(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
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
                '1. <code>/requests <user_id></code>\n' +
                '2. Reply <code>/requests</code> to a user\'s message',
                quote=True
            )
            return
        else:
            target_user_id = replied_to.from_user.id


    user_id = db.get_user(target_user_id)

    if user_id is None:
        await message.reply_text(
            text='There are no records for the user yet.',
            quote=True
        )
        return

    user_requests = db.get_user_requests(target_user_id)
    stats_text = f'There are currently {len(user_requests)} requests registered in database for this user.\n'

    if len(user_requests) > 0:

        cur_time = datetime.now()
        group_id = int(str(GROUP_ID)[4:])
        def get_req_time(req):
            return req['req_time']

        english_requests = [req for req in user_requests if req['is_english']]
        english_requests_fulfilled = [req for req in english_requests if req['fulfill_time'] is not None]
        non_english_requests = [req for req in user_requests if not req['is_english']]
        non_english_requests_fulfilled = [req for req in non_english_requests if req['fulfill_time'] is not None]

        stats_text += f"\n<u>Eng. Req. Fulfilled</u>: {len(english_requests_fulfilled)} out of {len(english_requests)}\n"
        stats_text += f"<u>Non-Eng. Req. Fulfilled</u>: {len(non_english_requests_fulfilled)} out of {len(non_english_requests)}\n"

        req_by_req_time = sorted(user_requests, key=get_req_time)
        last_req = req_by_req_time[-1]

        stats_text += f'\nThe {html_message_link(group_id, last_req["message_id"], "last one")} was {format_time_diff(cur_time, last_req["req_time"])}'

        if last_req['fulfill_time'] is not None:
            stats_text += f' and it was {html_message_link(group_id, last_req["fulfill_message_id"], "fulfilled")} {format_time_diff(cur_time, last_req["fulfill_time"])}'

    await message.reply_text(
                text=stats_text,
                quote=True
            )


@app.on_message(filters=START_COMMAND_FILTER, group=4)
async def start_command(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
        membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
        if membership.status not in ['administrator', 'creator']:
            return

    await message.reply_text(
        text="Hi I am up and tracking the requests 😎",
        quote=True
    )

@app.on_message(filters=LIMITS_COMMAND_FILTER, group=5)
async def limits_command(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
        membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
        if membership.status not in ['administrator', 'creator']:
            return

    limits_message = f'<b>These are the current limits</b>:\n\n' + \
                    f'<u>Eng. Requests</u>: {REQ_TIMES["eng"]["value"]}{REQ_TIMES["eng"]["type"]}\n' + \
                    f'<u>Non-Eng. Requests</u>: {REQ_TIMES["non_eng"]["value"]}{REQ_TIMES["non_eng"]["type"]}'

    await message.reply_text(
        text=limits_message,
        quote=True
    )

@app.on_message(filters=DROP_DB_COMMAND_FILTER, group=6)
async def drop_db_command(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
        membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
        if membership.status != 'creator':
            return

    db.drop_database()
    db.create_schema()

    await message.reply_text(
        text="Successfully dropped database",
        quote=True
    )


@app.on_message(filters=CLEAR_LAST_REQUEST_COMMAND_FILTER, group=7)
async def del_last_req_command(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
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
                '1. <code>/dellastreq <user_id></code>\n' +
                '2. Reply <code>/dellastreq</code> to a user\'s message',
                quote=True
            )
            return
        else:
            target_user_id = replied_to.from_user.id

    target_user = None
    try:
        target_user = await client.get_chat_member(GROUP_ID, target_user_id)
    except Exception as _:
    # if target_user is None:
        await message.reply_text(
            text="Not a valid id",
            quote=True
        )
        return

    target_user = target_user.user

    user_id = db.get_user(target_user_id)

    if user_id is None:
        await message.reply_text(
            text='There are no records for the user yet.',
            quote=True
        )
        return

    user_requests = db.get_user_requests(target_user_id)

    if len(user_requests) == 0:
        await message.reply_text(
            text='There are no records for the user yet.',
            quote=True
        )
        return

    cur_time = datetime.now()
    group_id = int(str(GROUP_ID)[4:])
    def get_req_time(req):
        return req['req_time']

    req_by_req_time = sorted(user_requests, key=get_req_time)
    last_req = req_by_req_time[-1]

    db.delete_request(target_user_id, last_req['message_id'])

    await message.reply_text(
                text=f'{html_message_link(group_id, last_req["message_id"], "Last request")} of ' +
                    f'{target_user.mention(target_user.first_name)} from ' +
                    f'{format_time_diff(cur_time, last_req["req_time"])} has been deleted',
                quote=True
            )

@app.on_message(filters=STATS_COMMAND_FILTER, group=8)
async def get_global_stats(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
        membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
        if membership.status not in ['administrator', 'creator']:
            return

    body = message.text
    if body is None:
        return

    all_requests = db.get_requests()
    all_requests_fulfilled = [req for req in all_requests if req['fulfill_time'] is not None]
    english_requests = [req for req in all_requests if req['is_english']]
    english_requests_fulfilled = [req for req in english_requests if req['fulfill_time'] is not None]
    non_english_requests = [req for req in all_requests if not req['is_english']]
    non_english_requests_fulfilled = [req for req in non_english_requests if req['fulfill_time'] is not None]

    stats_text = f'Stats for {GROUP_NAME}\n\n'
    stats_text += f'<u>Eng. Req. Fulfilled</u>: {len(english_requests_fulfilled)} out of {len(english_requests)}\n'
    stats_text += f'<u>Non-Eng. Req. Fulfilled</u>: {len(non_english_requests_fulfilled)} out of {len(non_english_requests)}\n'
    stats_text += f'\n<u>Total Req. Fulfilled</u>: {len(all_requests_fulfilled)} out of {len(all_requests)}\n'

    await message.reply_text(
        text=stats_text,
        quote=True
    )


@app.on_message(filters=DONE_COMMAND_FILTER, group=9)
async def mark_request_done(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
        membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
        if membership.status not in ['administrator', 'creator']:
            return

    body = message.text
    if body is None:
        return

    replied_to = message.reply_to_message
    if (replied_to is None) or (not is_a_request(replied_to)):
        await message.reply(
            text="Please reply to a request message",
            quote=True
        )
        return

    target_user = replied_to.from_user
    if target_user is None:
        await message.reply(
            text="Couldn't find any user in the replied message :panick:",
            quote=True
        )
        return

    user_id = db.get_user(target_user.id)
    if user_id is None:
        db.add_user(target_user.id)
    user_id = target_user.id

    is_english = is_english_request(replied_to)
    if db.get_request(user_id, replied_to.message_id)[0] is None:
        db.register_request(user_id, is_english, replied_to.message_id)

    db.register_request_fulfillment(user_id, replied_to.message_id, message.message_id)

    group_id = int(str(GROUP_ID)[4:])
    await message.reply_text(
        text=f"{html_message_link(group_id, replied_to.message_id, 'Request')} marked as fulfilled\n",
        quote=True
    )


@app.on_message(filters=PENDING_COMMAND_FILTER, group=10)
async def get_pending_requests(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
        membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
        if membership.status not in ['administrator', 'creator']:
            return

    body = message.text
    if body is None:
        return

    pending_requests = db.get_pending_requests()

    if len(pending_requests) == 0:
        await message.reply_text(
            text="There are no pending requests in records :)",
            quote=True
        )
        return

    def get_req_time(req):
        return req['req_time']

    pending_requests = sorted(pending_requests, key=get_req_time)

    pending_req_text = f'Here are the oldest pending requests:\n\n'

    group_id = int(str(GROUP_ID)[4:])
    cur_time = datetime.now()

    for indx,request in enumerate(pending_requests):

        # target_user = None
        # try:
        #     target_user = await client.get_chat_member(GROUP_ID, request['user_id'])
        # except Exception as _:
        # # if target_user is None:
        #     print(f"Error: {_}")
        #     continue

        # target_user = target_user.user
        pending_req_text += f'{indx+1}. {html_message_link(group_id, request["message_id"], f"Request {indx+1}")}, '
        # pending_req_text += f'by {target_user.mention(target_user.first_name)}, '
        pending_req_text += f'<i>{format_time_diff(cur_time, request["req_time"])}</i>\n'

    await message.reply_text(
        text=pending_req_text,
        quote=True
    )


@app.on_message(filters=HELP_COMMAND_FILTER, group=11)
async def help_message(client: Client, message: Message):

    user = message.from_user
    if user is None:
        return

    if message.chat.id == GROUP_ID and user.id not in SUDO_USERS:
        membership: ChatMember = await client.get_chat_member(chat_id=GROUP_ID, user_id=user.id)
        if membership.status not in ['administrator', 'creator']:
            return

    body = message.text
    if body is None:
        return

    help_message = "<u>Commands:</u>\n" +\
                "- /start : Get confirmation that bot is up (SUDO + ADMINS)\n" +\
                "- /requests : Get user requests stats. Pass in user ID or reply to user's message (SUDO + ADMINS)\n" +\
                "- /stats : Get global request stats (SUDO + ADMINS)\n" +\
                "- /limits : Get current request limits (SUDO + ADMINS)\n" +\
                "- /done : Manually mark a request as completed incase the media is not replied to request (SUDO + ADMINS)\n" +\
                "- /dellastreq : Delete the latest registered request of a user. Pass in user ID or reply to user's message (SUDO + ADMINS)\n" +\
                "- /dropdb : Delete the whole database ⚠️ (SUDO + OWNER)\n"

    await message.reply_text(
        text=help_message,
        quote=True
    )


app.run()
