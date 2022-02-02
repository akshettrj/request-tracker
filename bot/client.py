from pyrogram import ContinuePropagation
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message

from bot import (
    SESSION_STRING, BOT_TOKEN, API_HASH, API_ID,
    logger
)
from bot.filters import CustomFilters
from bot.helpers.utils import is_admin, is_sudo_user

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


@app.on_message(filters=CustomFilters.start_cmd_filter)
async def start_command(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    await message.reply_text(
        text="Hi I am up and tracking the requests 😎",
        quote=True
    )

    raise ContinuePropagation
