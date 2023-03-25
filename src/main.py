import json
import uvloop
import zipfile
import time

from pyrogram import Client, filters
import pylast

import markup
import const


uvloop.install()
app = Client(const.SESSION_NAME,
    api_id=const.TG_API_ID,
    api_hash=const.TG_API_HASH,
    bot_token=const.BOT_TOKEN
)
network = pylast.LastFMNetwork(const.FM_API_KEY, const.FM_API_SECRET)
with open(const.USER_SETTINGS_PATH) as f:
    user_settings = json.load(f)


@app.on_message(filters.command('start'), group=-1)
async def start(client, message):
    user_id = message.from_user.id
    if str(user_id) not in user_settings:
        create_user_settings(user_id)
    user_settings[str(user_id)]['loading_file'] = False

    return await client.send_message(
        chat_id=user_id,
        text=const.START_MESSAGE, 
        reply_markup=markup.get_start_markup(user_settings[str(user_id)])
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'login'))
async def last_fm_login(client, query):
    user_id = query.from_user.id
    session_key_generator = pylast.SessionKeyGenerator(network)
    auth_url = session_key_generator.get_web_auth_url()
    user_settings[str(user_id)]['session_key_generator'] = session_key_generator
    user_settings[str(user_id)]['auth_url'] = auth_url

    if str(user_id) not in user_settings:
        create_user_settings(user_id)

    await client.answer_callback_query(query.id)  # Delete the loading circle
    return await query.message.edit_text(
        text=const.LOGIN_MESSAGE,
        reply_markup=markup.get_login_markup(auth_url)
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'auth_done'))
async def check_autorization(client, query):
    user_id = query.from_user.id
    session_key_generator = user_settings[str(user_id)]['session_key_generator']
    auth_url = user_settings[str(user_id)]['auth_url']

    try:
        session_key, username = session_key_generator.get_web_auth_session_key_username(auth_url)
        await client.answer_callback_query(query.id, const.AUTH_SUCCESS, show_alert=True)
        del user_settings[str(user_id)]['session_key_generator']
        del user_settings[str(user_id)]['auth_url']
        update_session_key_username(user_id, session_key, username)
        return await query.message.edit_text(
            const.START_MESSAGE, 
            reply_markup=markup.get_start_markup(user_settings[str(user_id)])
        )
    except pylast.WSError:
        await client.answer_callback_query(query.id, const.AUTH_ERROR, show_alert=True)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'logout'))
async def last_fm_logout(client, query):
    user_id = query.from_user.id

    if str(user_id) not in user_settings:
        create_user_settings(user_id)

    await client.answer_callback_query(query.id)  # Delete the loading circle
    return await query.message.edit_text(
        text=const.LOGOUT_MESSAGE,
        reply_markup=markup.get_logout_markup()
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'unauth_done'))
async def remove_authorization(client, query):
    user_id = query.from_user.id

    if str(user_id) not in user_settings:
        create_user_settings(user_id)

    update_session_key_username(user_id, session_key=None, username=None)
    await client.answer_callback_query(query.id, const.UNAUTH_SUCCESS, show_alert=True)
    return await query.message.edit_text(
        const.START_MESSAGE, 
        reply_markup=markup.get_start_markup(user_settings[str(user_id)])
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'back'))
async def back(client, query):
    user_id = query.from_user.id
    if str(user_id) not in user_settings:
        create_user_settings(user_id)
    user_settings[str(user_id)]['loading_file'] = False

    await client.answer_callback_query(query.id)  # Delete the loading circle
    return await query.message.edit_text(
        text=const.START_MESSAGE,
        reply_markup=markup.get_start_markup(user_settings[str(user_id)])
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'settings'))
async def settings(client, query):
    user_id = query.from_user.id
    if str(user_id) not in user_settings:
        create_user_settings(user_id)

    text = const.SETTINGS_MESSAGE.format(
        const.WRENCH, const.TIC if user_settings[str(user_id)]['loaded_history'] else const.CROSS
    )

    await client.answer_callback_query(query.id)  # Delete the loading circle
    return await query.message.edit_text(
        text=text,
        reply_markup=markup.get_settings_markup()
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'load_history'))
async def load_history(client, query):
    user_id = query.from_user.id
    if str(user_id) not in user_settings:
        create_user_settings(user_id)

    if not user_settings[str(user_id)]['session_key']:
        return await client.answer_callback_query(query.id, const.NOT_LOGGED_MESSAGE, show_alert=True)

    user_settings[str(user_id)]['loading_file'] = True

    await client.answer_callback_query(query.id)  # Delete the loading circle
    return await query.message.edit_text(
        text=const.LOAD_HISTORY_MESSAGE,
        reply_markup=markup.get_load_history_markup()
    )


@app.on_message(filters.create(lambda _, __, message: str(message.from_user.id) in user_settings and user_settings[str(message.from_user.id)]['loading_file']))
async def store_history(client, message):
    user_id = message.from_user.id
    if str(user_id) not in user_settings:
        create_user_settings(user_id)

    if not message.document or message.document.file_name[-4:] != '.zip':
        return await client.send_message(
            chat_id=user_id,
            text=const.INVALID_HISTORY_MESSAGE,
        )

    # TODO: add status for endsong_x.json
    status = await set_history_loading_status(client, user_id, message.document.file_name)
    history_zip = await client.download_media(message, in_memory=True)
    await update_history_loading_status(status, message.document.file_name, step=1)
    with zipfile.ZipFile(history_zip) as zip:
        await update_history_loading_status(status, message.document.file_name, step=2)
        endsongs = list(filter(lambda x: ('MyData/endsong' in x), zip.namelist()))
        for item in endsongs:
            with zip.open(item) as f:
                history_chunk = json.loads(f.read().decode('utf-8'))
                await merge_scrobbles(user_id, history_chunk)
    await update_history_loading_status(status, message.document.file_name, step=3)


@app.on_message(filters.command('now', prefixes=['/', '.', '!', '']), group=-1)
async def now(client, message):
    #TODO: check login
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name

    if str(user_id) not in user_settings:
        create_user_settings(user_id)
    user_settings[str(user_id)]['loading_file'] = False

    username = user_settings[str(user_id)]['username']
    user = network.get_user(username)
    playing_track = user.get_now_playing()
    plays = await get_playcount(playing_track, user_id)
    track_cover_url = playing_track.get_cover_image()
    
    caption = f'<i>{user_first_name} is listening to:</i>\n{playing_track}\n{plays} plays'

    #TODO: increase image resolution with Spotify API
    return await client.send_photo(
        chat_id=user_id,
        photo=track_cover_url,
        caption=caption
    )


async def get_playcount(playing_track, user_id):
    lastfm_playcount = playing_track.get_userplaycount()
    artist = playing_track.artist.name
    track_name = playing_track.title
    for item in user_settings[str(user_id)]['scrobbles_before_lastfm']:
        if item['artist'] == artist and item['track_name'] == track_name:
            return lastfm_playcount + item['scrobbles']
    return lastfm_playcount


async def set_history_loading_status(client, user_id, file_name):
    emojis = [const.RADIO_BUTTON] + [const.HOURGLASS] * 2
    return await client.send_message(
        chat_id=user_id,
        text=const.STATUS_HISTORY_LOAD_MESSAGE.format(file_name, *emojis)
    )


async def update_history_loading_status(message, file_name, step):
    emojis = [const.TIC if i < step else (const.RADIO_BUTTON if i == step else const.HOURGLASS) for i in range(3)]
    await message.edit_text(text=const.STATUS_HISTORY_LOAD_MESSAGE.format(file_name, *emojis))


async def merge_scrobbles(user_id, history_chunk):
    username = user_settings[str(user_id)]['username']
    user = network.get_user(username)
    registration_unixtime = user.get_unixtime_registered()
    for scrobble in history_chunk:
        if scrobble['ms_played'] > 30000:
            scrobble_timestamp = time.strptime(scrobble['ts'], const.DATETIME_FORMAT)
            scrobble_unixtime = int(time.mktime(scrobble_timestamp))
            artist = scrobble['master_metadata_album_artist_name']
            track_name = scrobble['master_metadata_track_name']
            album = scrobble['master_metadata_album_album_name']
            if scrobble_unixtime < registration_unixtime:
                index = get_track_index(user_settings[str(user_id)]['scrobbles_before_lastfm'], artist, track_name)
                if index:
                    user_settings[str(user_id)]['scrobbles_before_lastfm'][index]['scrobbles'] += 1
                    if scrobble_unixtime < user_settings[str(user_id)]['scrobbles_before_lastfm'][index]['unixtime_firstlisten']:
                        user_settings[str(user_id)]['scrobbles_before_lastfm'][index]['unixtime_firstlisten'] = scrobble_unixtime
                else:
                    user_settings[str(user_id)]['scrobbles_before_lastfm'].append({
                            'artist': artist, 
                            'track_name': track_name,
                            'album': album,
                            'scrobbles': 1,
                            'unixtime_firstlisten': scrobble_unixtime
                    })
    dump_user_settings()


def get_track_index(scrobbles, artist, track_name):
    for i, item in enumerate(scrobbles):
        if item['artist'] == artist and item['track_name'] == track_name:
            return i
    return None
                

def create_user_settings(user_id):
    # user_id is stored as string because json.dump() would generate
    # duplicate if we use int, since it would eventually converted in a string
    user_settings[str(user_id)] = {
        'session_key': None,
        'username': None,
        'loaded_history': False,
        'loading_file': False, 
        'scrobbles_before_lastfm': []
    }
    dump_user_settings()


def update_session_key_username(user_id, session_key, username):
    user_settings[str(user_id)]['session_key'] = session_key
    user_settings[str(user_id)]['username'] = username
    dump_user_settings()


def dump_user_settings():
    with open(const.USER_SETTINGS_PATH, 'w') as f:
        json.dump(user_settings, f, indent=4)


if __name__ == '__main__':
    app.run()
