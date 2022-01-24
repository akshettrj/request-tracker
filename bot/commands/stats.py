from datetime import datetime
import os
import matplotlib.pyplot as plt

from pyrogram import ContinuePropagation
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message

from bot import ( DB, GROUP_ID, NAME_CACHE, REQ_TIMES, HELP_DATA,
        GRAPH_FULFILLED_COLOR, GRAPH_REQUESTS_COLOR )
from bot.client import app
from bot.filters import CustomFilters
from bot.helpers.utils import (
    is_admin, is_sudo_user, get_main_group_name,
    html_message_link, sort_help_data,
    format_time_diff, format_date
)


HELP_DATA += [["leaderboard", "Get the current requests fulfillment leaderboard", ["SUDO", "ADMIN"]]]
HELP_DATA += [["limits", "Get the current request limits configured in the bot", ["SUDO", "ADMIN"]]]
HELP_DATA += [["requests", "Get the total number of requests made by a person. Pass in User ID or reply to a message", ["SUDO", "ADMIN"]]]
HELP_DATA += [["stats", "Get the requests stats for the group", ["SUDO", "ADMIN"]]]
sort_help_data()


@app.on_message(filters=CustomFilters.limits_cmd_filter)
async def limits_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    limits_message  = f'<b>These are the current limits</b>:\n\n'
    limits_message += f'<u>Eng. Requests</u>: {REQ_TIMES["eng"]["full"]}\n'
    limits_message += f'<u>Non-Eng. Requests</u>: {REQ_TIMES["non_eng"]["full"]}'

    await message.reply_text(
        text=limits_message,
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.requests_cmd_filter)
async def requests_cmd(client: Client, message: Message):

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
                '1. <code>/requests <user_id></code>\n' +
                '2. Reply <code>/requests</code> to a user\'s message',
                quote=True
            )
            raise ContinuePropagation
        else:
            target_user_id = replied_to.from_user.id


    user_id = DB.get_user(target_user_id)

    if user_id is None:
        await message.reply_text(
            text='There are no records for the user yet.',
            quote=True
        )
        return

    ( english_fulfilled, non_english_fulfilled,
    english_not_fulfilled, non_english_not_fulfilled ) = DB.get_user_stats(target_user_id)

    total_requests = sum((english_fulfilled, non_english_fulfilled,
    english_not_fulfilled, non_english_not_fulfilled))

    stats_text = f'There are currently {total_requests} requests registered in database for this user.\n'

    if total_requests > 0:

        cur_time = datetime.now()
        group_id = int(str(GROUP_ID)[4:])

        english_requests = english_fulfilled + english_not_fulfilled
        non_english_requests = non_english_fulfilled + non_english_not_fulfilled

        stats_text += f"\n<b>Eng. Requests</b>: {english_fulfilled} / {english_requests}\n"
        stats_text += f"<b>Non-Eng. Requests</b>: {non_english_fulfilled} / {non_english_requests}\n"

        last_req = DB.get_user_last_request(target_user_id)

        if last_req['message_id'] is None or last_req['req_time'] is None:
            raise ContinuePropagation

        stats_text += f'\nThe {html_message_link(group_id, last_req["message_id"], "last one")} was {format_time_diff(cur_time, last_req["req_time"])}'

        if last_req['fulfill_time'] is not None and last_req['fulfill_message_id'] is not None:
            stats_text += f' and it was {html_message_link(group_id, last_req["fulfill_message_id"], "fulfilled")} {format_time_diff(cur_time, last_req["fulfill_time"])}'

    await message.reply_text(
        text=stats_text,
        quote=True
    )

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.stats_cmd_filter)
async def stats_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    ( english_fulfilled, non_english_fulfilled,
    english_not_fulfilled, non_english_not_fulfilled ) = DB.get_global_stats()

    all_requests_fulfilled = english_fulfilled + non_english_fulfilled
    english_requests = english_fulfilled + english_not_fulfilled
    non_english_requests = non_english_fulfilled + non_english_not_fulfilled

    all_requests = english_requests + non_english_requests

    start_date = None
    total_days = 1
    oldest_req_time = DB.get_oldest_request_time()
    if oldest_req_time is not None:
        start_date = oldest_req_time[0].date()
        curr_time = datetime.now().date()
        total_days = (curr_time-start_date).days
        if total_days == 0:
            total_days = 1

    try:
        group_name = await get_main_group_name(client)
    except Exception as ex:
        await message.reply_text(
            text=f"Error while retrieving Group's name:\n\n<code>{ex}</code>",
            quote=True
        )
        raise ContinuePropagation

    fulfill_rate = round((all_requests_fulfilled * 100) / all_requests, 2)

    stats_text = f'<b>Stats for {group_name} {f"since {format_date(start_date)}" if start_date is not None else ""}</b>\n\n'
    stats_text += f'<b>Eng. Requests</b> : {english_fulfilled} / {english_requests}\n'
    stats_text += f'<b>Non-Eng. Requests</b> : {non_english_fulfilled} / {non_english_requests}\n\n'
    stats_text += f'<b>Total Requests Fulfilled</b> : {all_requests_fulfilled} / {all_requests}\n\n'
    if oldest_req_time is not None:
        stats_text += f'<b>Fulfill Rate</b> : {fulfill_rate} %\n'
        stats_text += f'<b>Avg Req/day</b> : {round(all_requests / total_days, 2)} req/day'

    weekly_stats = DB.get_weekly_stats()
    x_label = [f"Week {wn}" for wn in range(1, len(weekly_stats)+1)]
    x_requests = [i - 0.25 for i in range(1, len(weekly_stats) + 1)]
    x_fulfilled = [i for i in range(1, len(weekly_stats) + 1)]
    x_mid = [i - 0.125 for i in range(1, len(weekly_stats) + 1)]
    y_requests = [stat[0] for stat in weekly_stats]
    y_fulfilled = [stat[1] for stat in weekly_stats]

    plt.clf()
    plt.bar(x_requests, y_requests, color=GRAPH_REQUESTS_COLOR, label="Requests", width=0.25)
    plt.bar(x_fulfilled, y_fulfilled, color=GRAPH_FULFILLED_COLOR, label="Fulfilled", width=0.25)
    plt.title(f"Weekly Stats for {group_name}")
    plt.xticks(x_mid, x_label)
    plt.legend()
    plt.savefig("./weekly_stats.png")

    await message.reply_photo(
        photo="./weekly_stats.png",
        caption=stats_text,
        quote=True
    )

    os.remove("./weekly_stats.png")

    raise ContinuePropagation


@app.on_message(filters=CustomFilters.leaderboard_cmd_filter)
async def leaderboard_cmd(client: Client, message: Message):

    user = message.from_user
    if user is None:
        raise ContinuePropagation

    if (not await is_sudo_user(user)) and (not await is_admin(client, user)):
        raise ContinuePropagation

    results = DB.get_leaderboard()
    results = sorted(results)
    results.reverse()

    group_name = await get_main_group_name(client)

    leaderboard_text = f"🎧 Top Contributor of {group_name}\n\n"

    for pos, result in enumerate(results):

        fulfill_count, user_id = result
        user_details = NAME_CACHE[user_id] if user_id in NAME_CACHE.keys() else DB.get_user_details(user_id)

        if user_details is None:
            leaderboard_text += f"{pos+1}) <b>[id:{user_id}]</b> ({fulfill_count} filled)\n"
            continue

        name, _ = user_details['name'], user_details['user_name']

        leaderboard_text += f'{pos+1}) <a href="tg://user?id={user_id}">{name}</a> ({fulfill_count} filled)\n'

    await message.reply_text(
        text=leaderboard_text,
        quote=True
    )
