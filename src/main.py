import uvloop

from pyrogram import Client, filters

import callbacks
import commands
from const import SESSION_NAME, TG_API_ID, TG_API_HASH, BOT_TOKEN
                

uvloop.install()
app = Client(SESSION_NAME,
    api_id=TG_API_ID,
    api_hash=TG_API_HASH,
    bot_token=BOT_TOKEN
)


@app.on_message(filters.command('start', prefixes=['/', '.', '!']))
async def start_caller(client, message):
    await commands.start(client, message)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'login'))
async def lastfm_login_caller(client, query):
    await callbacks.lastfm_login(client, query)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'auth_done'))
async def check_autorization_caller(client, query):
    await callbacks.check_autorization(client, query)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'logout'))
async def lastfm_logout_caller(client, query):
    await callbacks.lastfm_logout(client, query)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'unauth_done'))
async def remove_authorization_caller(client, query):
    await callbacks.remove_authorization(client, query)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'back'))
async def back_caller(client, query):
    await callbacks.back(client, query)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'settings'))
async def settings_caller(client, query):
    await callbacks.settings(client, query)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'load_history'))
async def load_history_caller(client, query):
    await callbacks.load_history(client, query)


@app.on_message(group=1)
async def store_history_caller(client, message):
    await callbacks.store_history(client, message)


@app.on_message(filters.command(['mood', 'cur', 'now'], prefixes=['/', '.', '!']))
async def mood_caller(client, message):
    await commands.mood(message)


@app.on_callback_query(filters.create(lambda _, __, query: 'fire' in query.data))
async def send_fire_caller(client, query):
    await callbacks.send_fire(client, query)


@app.on_message(filters.command(['collage', 'clg'], prefixes=['/', '.', '!']))
async def collage_command_caller(client, message):
    await commands.collage_command(client, message)


if __name__ == '__main__':
    app.run()
