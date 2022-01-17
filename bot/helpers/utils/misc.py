from functools import cmp_to_key
from bot import ( EXCLUDED_HASHTAGS, HELP_DATA, NAME_CACHE )
from pyrogram.types.messages_and_media.message import Message, Str


def is_a_request(message: Message) -> bool:

    if message.text is None:
        return False

    body: Str = message.text
    body_lines = body.split('\n')

    first_line_words = body_lines[0].split()
    first_line_words = [i.lower() for i in first_line_words if i.lower() not in EXCLUDED_HASHTAGS]

    if "#request" in first_line_words and "#audiobook" in first_line_words:
        return True

    return False


def is_english_request(message: Message):

    if message.text is None:
        return False

    body: Str = message.text
    body_lines = body.split('\n')

    first_line_words = body_lines[0].split()
    first_line_words = [i.lower() for i in first_line_words if i.lower() not in EXCLUDED_HASHTAGS]

    if (
        len(first_line_words) == 2 and
        "#audiobook" in first_line_words and
        "#request" in first_line_words
    ):
        return True

    return False


def html_message_link(grp_id: int, msg_id: int, text: str):
    return f'<a href="https://t.me/c/{grp_id}/{msg_id}">{text}</a>'


def sort_help_data():

    global HELP_DATA
    globals()["HELP_DATA"] = sorted(HELP_DATA, key=cmp_to_key(lambda i1, i2: (i1[0] < i2[0])))


def clear_name_cache():

    global NAME_CACHE
    NAME_CACHE = {}
