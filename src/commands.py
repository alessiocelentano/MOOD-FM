import re

from pylast import PERIOD_OVERALL

from cache import users_list, update_user, dump_users
import collage
import const
import markup
import misc
from network import network
from spotify import get_spotify_track_infos


async def start(client, message):
    user = await misc.get_user_instance(message.from_user.id)
    user.restore_state()
    update_user(user)
    dump_users()

    await client.send_message(
        chat_id=message.chat.id,
        text=const.START_MESSAGE, 
        reply_markup=markup.get_start_markup(user.session_key),
        disable_web_page_preview=False
    )


async def mood(message):
    user = await misc.get_user_instance(message.from_user.id)
    lastfm_user = network.get_user(user.name)
    user.restore_state()
    update_user(user)
    dump_users()

    if not user.session_key:
        return await message.reply_text(text=const.NOT_LOGGED_MESSAGE)
    
    playing_track = lastfm_user.get_now_playing()
    if not playing_track:
        return await message.reply_text(
            text=const.MOOD_ERROR.format(
                cross_emoji=const.CROSS,
                user_firstname=message.from_user.first_name
            )
        )

    # TODO: and if the track is not on Spotify?
    track, artists, cover_url = get_spotify_track_infos(playing_track)
    plays = user.get_playcount(playing_track)
    caption = const.MOOD_MESSAGE.format(
        message=message,
        fires_received=user.fires,
        track=track,
        artists=artists,
        plays=plays,
        loved_song_emoji=misc.get_loved_song_emoji(plays),
        const=const
    )

    plays_in_a_row = misc.get_plays_in_a_row(lastfm_user, playing_track)
    if plays_in_a_row > 1:
        caption += '\n' + const.PLAYS_IN_A_ROW.format(const.REPEAT_ONE, plays_in_a_row)

    # Here we pick only the first CALLBACK_DATA_MAX characters of track
    # and artists to avoid callback_data from being too large
    # (that would prevent the message sending) 
    await message.reply_photo(
        photo=cover_url,
        caption=caption,
        reply_markup=markup.get_mood_markup(
            user_id=user.id,
            fires=user.get_track_fires(artists, track),
            track=track[:const.CALLBACK_DATA_MAX],
            artists=artists[:const.CALLBACK_DATA_MAX]
        )
    )


async def collage_command(client, message):
    user = await misc.get_user_instance(message.from_user.id)
    lastfm_user = network.get_user(user.name)
    user.restore_state()
    update_user(user)
    dump_users()

    if not user.session_key:
        return await message.reply_text(text=const.NOT_LOGGED_MESSAGE)

    args = re.split(r' ', message.text)
    if len(args) > 5:
        return await message.reply_text(
            text=const.COLLAGE_ERROR,
            disable_web_page_preview=False
        )

    size = misc.get_size(message.text)
    time_range = misc.get_time_range(message.text)
    type = misc.get_top_type(message.text)
    clean = 'clean' in message.text

    valid_args = len([i for i in [size, time_range, type, clean] if i])
    args_warning = const.COLLAGE_ARGS_WARNING if valid_args < len(args) - 1 else ''

    size = size or (const.DEFAULT_COLLAGE_COLUMNS, const.DEFAULT_COLLAGE_ROWS)
    time_range = time_range or PERIOD_OVERALL
    type = type or const.TRACK
    
    collage_message = await client.send_message(
        chat_id=message.chat.id,
        text=const.LOADING_COLLAGE_MESSAGE
    )

    top_items_infos = await collage.get_top_items_infos(user, lastfm_user, size, time_range, type)
    collage_image = await collage.create_collage(
        items=top_items_infos,
        size=size,
        type=type,
        clean=clean
    )
    caption = const.COLLAGE_MESSAGE.format(
        message=message,
        size=size,
        type_emoji=misc.get_type_emoji(type), 
        type=type.capitalize(),
        time_emoji=const.TIME,
        time=misc.prettify_time_range(time_range)
    )

    await message.reply_photo(
        photo=collage_image,
        caption=caption+args_warning
    )
    await collage_message.delete()


async def tutorial(client, message):
    user = await misc.get_user_instance(message.from_user.id)
    user.restore_state()
    update_user(user)
    dump_users()

    await client.send_message(
        chat_id=message.chat.id,
        text=const.TUTORIAL_MESSAGE,
        disable_web_page_preview=False
    )


async def broadcast(client, message):
    if message.from_user.id != const.BROADCASTER_ID:
        return

    text = re.sub(r'/broadcast', '', message.text)
    for u in users_list:
        await client.send_message(
            chat_id=int(u),
            text=text
        )
