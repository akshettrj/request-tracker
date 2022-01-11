# Rᴇǫᴜᴇsᴛ Tʀᴀᴄᴋᴇʀ

Track and get stats for Audiobooks requests in your Telegram Group

## Cᴏɴғɪɢᴜʀᴀᴛɪᴏɴ

* There are two ways of configuring the bot:
    1. Use `config.env` by creating a copy of `sample_config.env` and edit the values
    2. Set Environment Variables
* Don't use both ways at the same time 🥴

### Vᴀʀɪᴀʙʟᴇs

| Nᴀᴍᴇ                | Dᴇsᴄʀɪᴘᴛɪᴏɴ                                                                                      | Dᴇғᴀᴜʟᴛ              |
| :-----------------: | ------------------------------------------------------------------------------------------------ | :------------------: |
| `API_ID`            | Get from my.telegram.org                                                                         | -                    |
| `API_HASH`          | Get from my.telegram.org                                                                         | -                    |
| `SESSION_STRING`    | Use either BOT_TOKEN or SESSION_STRING (Given Preference)                                        | -                    |
| `BOT_TOKEN`         | Use either BOT_TOKEN or SESSION_STRING                                                           | -                    |
| `SUDO_USERS`        | Space separated user IDs                                                                         | -                    |
| `GROUP_ID`          | ID of the group where requests are to be tracked                                                 | -                    |
| `GROUP_NAME`        | Name of the group (will be used in stats messages)                                               | -                    |
| `EZBOOKBOT_ID`      | ID of the EzBook Bot (which will fulfill requests, will be useful only when using SESSION_STRING | "1699727751"         |
| `DATABASE_URL`      | URL for connecting with PostgreSQL database.                                                     | -                    |
| `ENG_REQ_TIME`      | See information below                                                                            | "8d"                 |
| `NON_ENG_REQ_TIME`  | See information below                                                                            | "15d"                |
| `EXCLUDED_HASHTAGS` | The Hashtags in the request message which will not be considered as a language like #hindi etc.  | "#scribd #storytel"  |

* `ENG_REQ_TIME` and `NON_ENG_REQ_TIME` are the time periods of waiting after getting an English and Non-English audiobook request fulfilled.
* Both can take values specified by following units:
    * `d`: days
    * `min`: minutes
    * `s`: seconds
* At one time, only one unit can be used i.e. you can have values like `7d`, `4min`, `10s` but not values like `7d 10min`
* Example: If you set `ENG_REQ_TIME` to `1d`, then the user can request a new Audiobook the next day after requesting or fulfillment of last request.

## Aᴠᴀɪʟᴀʙʟᴇ Cᴏᴍᴍᴀɴᴅs

| Cᴏᴍᴍᴀɴᴅ             | Dᴇsᴄʀɪᴘᴛɪᴏɴ                                                                                      | Pᴇʀᴍɪssɪᴏɴs   |
| :-----------------: | ------------------------------------------------------------------------------------------------ | :---------:   |
| `/start`            | Get confirmation that bot is up                                                                  | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/requests`         | Get user requests stats. Pass in user ID or reply to user's message                              | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/stats`            | Get global request stats                                                                         | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/pending`          | Get current pending requests                                                                     | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/lastfilled`       | Get the latest fulfilled request                                                                 | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/limits`           | Get current request limits                                                                       | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/done`             | Manually mark a request as completed incase the media is not replied to request                  | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/notdone`          | Manually mark a request as pending incase ezbootbot sends wrong file                             | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/dellastreq`       | Delete the latest registered request of a user. Pass in user ID or reply to user's message       | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/delreq`           | Delete request based on message id. Pass in message_id or reply to request message               | Sᴜᴅᴏ + Aᴅᴍɪɴs |
| `/dropdb`           | Delete the whole database ⚠️                                                                      | Sᴜᴅᴏ + Oᴡɴᴇʀ  |


## Pʀᴏᴊᴇᴄᴛ Sᴛʀᴜᴄᴛᴜʀᴇ

```
.
├── sample_config.env       -> Sample Config file
├── requirements.txt        -> Python packages requirements
├── README.md
├── Procfile                -> Heroku
├── LICENSE
├── gen_session.py          -> Generate SESSION_STRING locally
├── bot                     -> All the code resides here
│  ├── helpers              -> Some database and other helper functions
│  │  ├── utils.py
│  │  └── database.py
│  ├── __main__.py          -> All the Pyrogram update handlers are here
│  └── __init__.py          -> Reads configuration variables and set up filters for commands and updates
└── app.json
```
