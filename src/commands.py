import re

from pylast import PERIOD_OVERALL

from cache import update_user, dump_users
import collage
import const
import markup
from misc import get_user_instance, get_size, get_time_range, get_top_type, \
                get_type_emoji, prettify_time_range
from network import network
from spotify import get_spotify_track_infos


async def start(client, message):
    user = await get_user_instance(message.from_user.id)
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
    user = await get_user_instance(message.from_user.id)
    lastfm_user = network.get_user(user.name)
    user.restore_state()
    update_user(user)
    dump_users()

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
    track, artists, cover_url = get_spotify_track_infos(playing_track)
    plays = user.get_playcount(playing_track)
    loved_song_emoji = const.GLOWING_STAR + ' ' if plays > 100 else ''
    caption = const.MOOD_MESSAGE.format(
        user_firstname=message.from_user.first_name,
        user_url=f't.me/{message.from_user.username}',
        fires_received=user.fires,
        track=track,
        artists=artists,
        plays=plays,
        loved_song_emoji=loved_song_emoji,
        fire_emoji=const.FIRE,
        headphones_emoji=const.HEADPHONES
    )

    plays_in_a_row = get_plays_in_a_row(lastfm_user, playing_track)
    if plays_in_a_row > 1:
        caption += '\n' + const.PLAYS_IN_A_ROW.format(const.REPEAT_ONE, plays_in_a_row)

    # Here we pick only the first CALLBACK_DATA_MAX characters of track
    # and artists to avoid callback_data from being too large
    # (that would prevent the message sending) 
    await message.reply_photo(
        photo=cover_url,
        caption=caption,
        reply_markup=markup.get_mood_markup(
            user.id,
            user.get_track_fires(artists, track),
            track[:const.CALLBACK_DATA_MAX],
            artists[:const.CALLBACK_DATA_MAX]
        )
    )


def get_plays_in_a_row(lastfm_user, playing_track):
    recent_tracks = lastfm_user.get_recent_tracks(limit=99)
    for i in range(99):
        if recent_tracks[i].track.title != playing_track.title:
            return i + 1
    return i + 1



async def collage_command(client, message):
    user = await get_user_instance(message.from_user.id)
    lastfm_user = network.get_user(user.name)
    user.restore_state()
    update_user(user)
    dump_users()

    if not user.session_key:
        return await message.reply_text(
            text=const.NOT_LOGGED_MESSAGE
        )

    args = re.split(r' ', message.text)
    if len(args) > 5:
        return await message.reply_text(
            text=const.COLLAGE_ERROR,
            disable_web_page_preview=False
        )

    size = get_size(message.text)
    time_range = get_time_range(message.text)
    type = get_top_type(message.text)
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
    clg = await collage.create_collage(user, top_items_infos, size, time_range, type, clean=clean)
    caption = const.COLLAGE_MESSAGE.format(
        user_link=f't.me/{message.from_user.username}',
        first_name=message.from_user.first_name,
        size=size,
        type_emoji=get_type_emoji(type), 
        type=type.capitalize(),
        time_emoji=const.TIME,
        time=prettify_time_range(time_range)
    )

    await message.reply_photo(
        photo=clg,
        caption=caption + args_warning
    )
    await collage_message.delete()
