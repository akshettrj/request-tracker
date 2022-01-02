from datetime import datetime
from bot import EXCLUDED_HASHTAGS
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


def format_time_diff(t1: datetime, t2: datetime):
    t_diff = t1 - t2
    t_days = f"{t_diff.days} days " if t_diff.days > 0 else ""

    hours = (t_diff.seconds // 3600) % 24

    t_hours = f"{hours} hrs " if hours > 0 else ""

    mins = (t_diff.seconds // 60) % 60

    t_mins = ""
    if t_diff.days == 0 and mins != 0:
        t_mins = f"{mins} mins "

    t_secs = ""
    if t_diff.days == 0 and hours == 0 and mins == 0:
        t_secs = f"{t_diff.seconds % 60} s"

    return f"{t_days}{t_hours}{t_mins}{t_secs} ago"


def get_message_media(message: Message):

    if message.voice:
        return message.voice

    if message.audio:
        return message.audio

    doc = message.document

    if doc is None or doc.file_name is None:
        return None


    if (".zip" in doc.file_name) or (".opus" in doc.file_name):
        return doc

    return None

def time_gap_not_crossed(curr_time: datetime, old_time: datetime, gap):

    print(gap['value'])
    if gap['type'] == 'd':
        time_diff = curr_time.date() - old_time.date()
        return time_diff.days < gap['value']

    elif gap['type'] == 'min':
        time_diff = curr_time - old_time
        mins = time_diff.seconds // 60
        return mins < gap['value']

    elif gap['type'] == 's':
        time_diff = curr_time - old_time
        return time_diff.seconds < gap['value']
