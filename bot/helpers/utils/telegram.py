from time import time
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram.types.user_and_chats.chat_member import ChatMember
from pyrogram.types.user_and_chats.chat_permissions import ChatPermissions
from pyrogram.types.user_and_chats.user import User

from bot import ( GROUP_ID, SUDO_USERS )


async def is_admin(client: Client, user: User):

    membership: ChatMember = await client.get_chat_member(
                                chat_id=GROUP_ID,
                                user_id=user.id
                            )
    return membership.status in ['administrator', 'creator']


async def is_owner(client: Client, user: User):

    membership: ChatMember = await client.get_chat_member(
                                chat_id=GROUP_ID,
                                user_id=user.id
                            )
    return membership.status == 'creator'


async def is_sudo_user(user: User):

    return user.id in SUDO_USERS


async def get_main_group_name(client: Client):

    chat = await client.get_chat(chat_id=GROUP_ID)
    return chat.title


def get_message_media(message: Message):

    if message.voice:
        return message.voice

    if message.audio:
        return message.audio

    doc = message.document

    if doc is None:
        return None

    return doc


async def mute_user(client: Client, user: User):

    await client.restrict_chat_member(
        chat_id=GROUP_ID,
        user_id=user.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=int(time() + 12 * 60 * 60)
    )
