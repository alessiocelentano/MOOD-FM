import json
import uvloop
import zipfile
import re

from pyrogram import Client, filters
import pylast
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from user import User
import markup
import const


uvloop.install()
app = Client(const.SESSION_NAME,
    api_id=const.TG_API_ID,
    api_hash=const.TG_API_HASH,
    bot_token=const.BOT_TOKEN
)
network = pylast.LastFMNetwork(
    api_key=const.FM_API_KEY,
    api_secret=const.FM_API_SECRET
)
spotify = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=const.SPOTIFY_CLIENT_ID,
        client_secret=const.SPOTIFY_CLIENT_SECRET
    )
)
with open(const.USERS_PATH) as f:
    users_list = json.load(f)


@app.on_message(filters.command('start'))
async def start(client, message):
    user = await get_user_instance(message.from_user.id)
    if user.is_loading_files:
        user.is_loading_files = False
        update_user(user)
        dump_users()

    await client.send_message(
        chat_id=message.chat.id,
        text=const.START_MESSAGE, 
        reply_markup=markup.get_start_markup(user.session_key),
        disable_web_page_preview=False
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'login'))
async def last_fm_login(client, query):
    user = await get_user_instance(query.from_user.id)

    user.session_key_generator = pylast.SessionKeyGenerator(network)
    user.auth_url = user.session_key_generator.get_web_auth_url()
    update_user(user)

    await client.answer_callback_query(query.id)  # Delete the loading circle
    await query.message.edit_text(
        text=const.LOGIN_MESSAGE,
        reply_markup=markup.get_login_markup(user.auth_url)
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'auth_done'))
async def check_autorization(client, query):
    user = await get_user_instance(query.from_user.id)

    try:
        user.session_key, user.name = user.session_key_generator.get_web_auth_session_key_username(user.auth_url)
        user.session_key_generator, user.auth_url = None, None
        update_user(user)
        dump_users()
        await client.answer_callback_query(query.id, const.AUTH_SUCCESS, show_alert=True)
        
        await query.message.edit_text(
            const.START_MESSAGE, 
            reply_markup=markup.get_start_markup(user.session_key)
        )

    except pylast.WSError:
        await client.answer_callback_query(query.id, const.AUTH_ERROR, show_alert=True)


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'logout'))
async def last_fm_logout(client, query):
    # user is not needed but we call the function
    # for the rare case that it's the user first action
    # in this way a new instance is created and stored
    await get_user_instance(query.from_user.id)

    await client.answer_callback_query(query.id)  # Delete the loading circle
    await query.message.edit_text(
        text=const.LOGOUT_MESSAGE,
        reply_markup=markup.get_logout_markup()
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'unauth_done'))
async def remove_authorization(client, query):
    user = await get_user_instance(query.from_user.id)
    user.session_key, user.name = None, None
    update_user(user)
    dump_users()

    await client.answer_callback_query(query.id, const.UNAUTH_SUCCESS, show_alert=True)
    await query.message.edit_text(
        const.START_MESSAGE, 
        reply_markup=markup.get_start_markup(user.session_key)
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'back'))
async def back(client, query):
    user = await get_user_instance(query.from_user.id)
    if user.is_loading_files:
        user.is_loading_files = False
        update_user(user)
        dump_users()

    await client.answer_callback_query(query.id)  # Delete the loading circle
    await query.message.edit_text(
        text=const.START_MESSAGE,
        reply_markup=markup.get_start_markup(user.session_key)
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'settings'))
async def settings(client, query):
    user = await get_user_instance(query.from_user.id)

    text = const.SETTINGS_MESSAGE.format(
        const.WRENCH,
        const.TIC if user.is_history_loaded else const.CROSS
    )

    await client.answer_callback_query(query.id)  # Delete the loading circle
    await query.message.edit_text(
        text=text,
        reply_markup=markup.get_settings_markup()
    )


@app.on_callback_query(filters.create(lambda _, __, query: query.data == 'load_history'))
async def load_history(client, query):
    user = await get_user_instance(query.from_user.id)

    if not user.session_key:
        return await client.answer_callback_query(
            query.id,
            const.NOT_LOGGED_MESSAGE,
            show_alert=True
        )

    if user.is_history_loaded:
        return await client.answer_callback_query(
            query.id,
            const.ALREADY_LOADED,
            show_alert=True
        )

    user.is_loading_files = True
    update_user(user)
    dump_users()

    await client.answer_callback_query(query.id)  # Delete the loading circle
    await query.message.edit_text(
        text=const.LOAD_HISTORY_MESSAGE,
        reply_markup=markup.get_load_history_markup()
    )


@app.on_message(group=1)
async def store_history(client, message):
    user = await get_user_instance(message.from_user.id)
    lastfm_user = network.get_user(user.name)
    registration_unixtime = lastfm_user.get_unixtime_registered()
    step = 1

    if not user.is_loading_files:
        return

    if not message.document or message.document.file_name[-4:] != '.zip':
        return await client.send_message(
            chat_id=message.chat.id,
            text=const.INVALID_HISTORY_MESSAGE,
        )

    user.is_loading_files = False
    
    status = await update_history_loading_status(
        message=message,
        file_names=[message.document.file_name], 
        step=0,
        client=client
    )
    history_zip = await client.download_media(message, in_memory=True)

    with zipfile.ZipFile(history_zip) as zip:
        endsongs = list(filter(lambda x: ('MyData/endsong' in x), zip.namelist()))
        for item in endsongs:
            await update_history_loading_status(
                message=status,
                file_names=[message.document.file_name] + endsongs,
                step=step
            )
            with zip.open(item) as f:
                scrobbles = json.loads(f.read().decode('utf-8'))
            user.store_scrobbles(scrobbles, registration_unixtime)
            step += 1

    user.is_history_loaded = True
    update_user(user)
    dump_users()
    await update_history_loading_status(
        message=status,
        file_names=[message.document.file_name] + endsongs,
        step=step
    )
    return await client.send_message(
        chat_id=message.chat.id,
        text=const.HISTORY_LOADED_MESSAGE
    )



@app.on_message(filters.command(['mood', 'cur', 'now'], prefixes=['/', '.', '!']))
async def mood(client, message):
    user = await get_user_instance(message.from_user.id)
    lastfm_user = network.get_user(user.name)
    if user.is_loading_files:
        user.is_loading_files = False
        update_user(user)
        dump_users()

    if not user.session_key:
        return await client.send_message(
            chat_id=message.chat.id,
            text=const.NOT_LOGGED_MESSAGE
        )
    
    playing_track = lastfm_user.get_now_playing()
    if not playing_track:
        return await client.send_message(
            chat_id=message.chat.id,
            text=const.MOOD_ERROR.format(
                cross_emoji=const.CROSS,
                user_firstname=message.from_user.first_name
            ),
        )

    # TODO: and if the track is not on Spotify?
    plays = get_playcount(user.scrobbles_before_lastfm, playing_track)
    search_result = spotify.search(playing_track, limit=1, type='track')['tracks']['items'][0]
    track_name = search_result['name']
    track_artists = ', '.join([artist['name'] for artist in search_result['artists']])
    track_cover_url = search_result['album']['images'][0]['url']
    
    caption = const.MOOD_MESSAGE.format(
        user_firstname=message.from_user.first_name,
        user_link=f't.me/{message.from_user.username}',
        fires_received=user.fires,
        track_name=track_name,
        artist_name=track_artists,
        plays=plays,
        fire_emoji=const.FIRE,
        headphones_emoji=const.HEADPHONES
    )

    # Here we pick only the first CALLBACK_DATA_MAX characters of track_name
    # and track_artists to avoid callback_data from being too large
    # (that would prevent the message sending) 
    await client.send_photo(
        chat_id=message.chat.id,
        photo=track_cover_url,
        caption=caption,
        reply_markup=markup.get_mood_markup(
            user.id,
            user.get_track_fires(track_artists, track_name),
            track_name[:const.CALLBACK_DATA_MAX],
            track_artists[:const.CALLBACK_DATA_MAX]
        )
    )


@app.on_callback_query(filters.create(lambda _, __, query: 'fire' in query.data))
async def send_fire(client, query):
    _, user_receiver_id, track_name, artists = re.split('/@/', query.data)
    user_sender = await get_user_instance(query.from_user.id)
    user_receiver = await get_user_instance(user_receiver_id)

    is_added = user_sender.toggle_fire_sending(user_receiver.id, artists, track_name)
    user_receiver.toggle_fire_addition(user_sender.id, artists, track_name)
    update_user(user_sender)
    update_user(user_receiver)
    dump_users()

    await query.message.edit_reply_markup(
        reply_markup=markup.get_mood_markup(
            user_receiver.id,
            user_receiver.get_track_fires(artists, track_name),
            track_name[:const.CALLBACK_DATA_MAX],
            artists[:const.CALLBACK_DATA_MAX]
        )
    )
    await client.answer_callback_query(
        query.id, 
        const.FIRE_ADDED if is_added else const.FIRE_REMOVED
    )


def get_playcount(scrobbles_before_lastfm, playing_track):
    lastfm_playcount = playing_track.get_userplaycount()
    artist = playing_track.artist.name
    track_name = playing_track.title

    for item in scrobbles_before_lastfm:
        if item['artist'] and artist in item['artist'] and item['track_name'] == track_name:
            return lastfm_playcount + item['scrobbles']

    return lastfm_playcount


async def update_history_loading_status(message, file_names, step, client=None):
    emojis = [const.TIC if i < step else (const.HOURGLASS if i == step else const.RADIO_BUTTON) for i in range(2)]
    if step == 0:
        return await client.send_message(
            chat_id=message.chat.id,
            text=const.STATUS_HISTORY_LOAD_MESSAGE.format(file_names[0], *emojis)
        )
    endsongs = file_names[1:]
    await message.edit_text(
        text = const.STATUS_HISTORY_LOAD_MESSAGE.format(file_names[0], *emojis) + get_endsongs_list(endsongs, step)
    )


def get_endsongs_list(endsongs, step):
    emojis = [const.TIC if i < step else (const.HOURGLASS if i == step else const.RADIO_BUTTON) for i in range(1, len(endsongs) + 1)]
    text = f'\n<i>{const.MAGNIFYING_GLASS} {len(endsongs) - 1} files found</i>\n'
    for emoji, file_name in zip(emojis, endsongs):
        text += f'{emoji} <code>{file_name}</code>\n'
    return text


async def get_user_instance(user_id):
    if str(user_id) in users_list:
        user_data = users_list[str(user_id)]
        user = User(**user_data)
    else:
        user = User(user_id)
        update_user(user)  # Create it, in this case
        dump_users()
    return user


def update_user(user):
    # id is stored as string because json.dump() would generate
    # duplicate if we use int, since it would eventually converted in a string
    users_list[str(user.id)] = {
        'id': user.id,
        'name': user.name,
        'session_key': user.session_key,
        'session_key_generator': user.session_key_generator,
        'auth_url': user.auth_url,
        'is_history_loaded': user.is_history_loaded,
        'is_loading_files': user.is_loading_files, 
        'fires_received': user.fires_received,
        'fires_sended': user.fires_sended,
        'scrobbles_before_lastfm': user.scrobbles_before_lastfm
    }


def dump_users():
    with open(const.USERS_PATH, 'w+') as f:
        json.dump(users_list, f, indent=4)


if __name__ == '__main__':
    app.run()
