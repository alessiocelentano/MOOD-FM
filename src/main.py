import json
import uvloop
import zipfile
import re

from pyrogram import Client, filters
import pylast

from user import User
import markup
import collage
from spotify import get_spotify_track_infos
from cache import users_list, update_user, dump_users
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


@app.on_message(filters.command('start'))
async def start(client, message):
    user = await get_user_instance(message.from_user.id)
    await restore_state(user)

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
    await restore_state(user)

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
    await restore_state(user)

    if not user.session_key:
        return await message.reply_text(
            text=const.NOT_LOGGED_MESSAGE
        )
    
    playing_track = lastfm_user.get_now_playing()
    if not playing_track:
        return await message.reply_text(
            text=const.MOOD_ERROR.format(
                cross_emoji=const.CROSS,
                user_firstname=message.from_user.first_name
            )
        )

    # TODO: and if the track is not on Spotify?
    track_name, track_artists, track_cover_url = get_spotify_track_infos(playing_track)
    plays = get_playcount(user.scrobbles_before_lastfm, playing_track)
    caption = const.MOOD_MESSAGE.format(
        user_firstname=message.from_user.first_name,
        user_url=f't.me/{message.from_user.username}',
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
    await message.reply_photo(
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
    _, user_receiver_id, track_name, artists = re.split(r'/@/', query.data)
    user_sender = await get_user_instance(query.from_user.id)
    user_receiver = await get_user_instance(user_receiver_id)

    if user_sender.id == user_receiver.id:
        return await client.answer_callback_query(
            query.id,
            const.AUTOFIRE
        )

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


@app.on_message(filters.command(['collage', 'clg'], prefixes=['/', '.', '!']))
async def clg(client, message):
    user = await get_user_instance(message.from_user.id)
    lastfm_user = network.get_user(user.name)
    await restore_state(user)

    if not user.session_key:
        return await message.reply_text(
            text=const.NOT_LOGGED_MESSAGE
        )

    args = re.split(r' ', message.text)
    if len(args) > 4:
        return await message.reply_text(
            text=const.COLLAGE_ERROR,
            disable_web_page_preview=False
        )

    size = get_size(message.text)
    time_range = get_time_range(message.text)
    type = get_top_type(message.text)

    valid_args = len([i for i in [size, time_range, type] if i])
    args_warning = const.COLLAGE_ARGS_WARNING if valid_args < len(args) - 1 else ''

    size = size or (const.DEFAULT_COLLAGE_COLUMNS, const.DEFAULT_COLLAGE_ROWS)
    time_range = time_range or pylast.PERIOD_OVERALL
    type = type or const.TRACK
    
    collage_message = await client.send_message(
        chat_id=message.chat.id,
        text=const.LOADING_COLLAGE_MESSAGE
    )

    covers_list = await collage.get_top_items_covers_url(lastfm_user, size, time_range, type)
    clg = await collage.create_collage(covers_list, size)
    caption = f'{message.from_user.first_name} {size[0]}x{size[1]} {time_range} {type} collage' 

    await message.reply_photo(
        photo=clg,
        caption=caption + args_warning
    )
    await collage_message.delete()


def get_size(text):
    size_match = re.search(r'\s([1-9]|10)x\1(?=\s|$)', text)
    if size_match:
        return tuple(int(group) for group in re.split(r'x', size_match.group(0)))
    return None


def get_time_range(text):
    if re.search(r'\s(7d(ays)?)|(1w(eek)?)(?=\s|$)', text):
        return pylast.PERIOD_7DAYS
    if re.search(r'\s1m(onths)?(?=\s|$)', text):
        return pylast.PERIOD_1MONTH
    if re.search(r'\s3m(onths)?(?=\s|$)', text):
        return pylast.PERIOD_3MONTHS
    if re.search(r'\s6m(onths)?(?=\s|$)', text):
        return pylast.PERIOD_6MONTHS
    if re.search(r'\s(12m(onths)?)|(1y(ear)?)(?=\s|$)', text):
        return pylast.PERIOD_12MONTHS
    if re.search(r'\s(overall)|(all(time)?)(?=\s|$)', text):
        return pylast.PERIOD_OVERALL
    return None


def get_top_type(text):
    if re.search(r'\sar(tist(s)?)?(?=\s|$)', text):
        return const.ARTIST
    if re.search(r'\sal(bum(s)?)?(?=\s|$)', text):
        return const.ALBUM
    if re.search(r'\str(ack(s)?)?(?=\s|$)', text):
        return const.TRACK
    return None



def get_playcount(scrobbles_before_lastfm, playing_track):
    try:
        lastfm_playcount = playing_track.get_userplaycount()
    except pylast.WSError:
        # It seems that get_userplaycount() can't be called when a track is too recent
        lastfm_playcount = 0
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


async def restore_state(user):
    if user.is_loading_files or user.session_key_generator:
        user.is_loading_files = False
        user.session_key_generator = None
        user.auth_url = None
        update_user(user)
        dump_users()


async def get_user_instance(user_id):
    if str(user_id) in users_list:
        user_data = users_list[str(user_id)]
        user = User(**user_data)
    else:
        user = User(user_id)
        update_user(user)  # Create it, in this case
        dump_users()
    return user


if __name__ == '__main__':
    app.run()
