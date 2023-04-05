import json
import re
from zipfile import ZipFile

from pylast import SessionKeyGenerator, WSError

from cache import update_user, dump_users
import const
import markup
from misc import get_user_instance, update_history_loading_status
from network import network


async def lastfm_login(client, query):
    user = await get_user_instance(query.from_user.id)

    user.session_key_generator = SessionKeyGenerator(network)
    user.auth_url = user.session_key_generator.get_web_auth_url()
    update_user(user)

    await client.answer_callback_query(query.id)  # Delete the loading circle
    await query.message.edit_text(
        text=const.LOGIN_MESSAGE,
        reply_markup=markup.get_login_markup(user.auth_url)
    )


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

    except WSError:
        await client.answer_callback_query(query.id, const.AUTH_ERROR, show_alert=True)


async def lastfm_logout(client, query):
    # user is not needed but we call the function
    # for the rare case that it's the user first action
    # in this way a new instance is created and stored
    await get_user_instance(query.from_user.id)

    await client.answer_callback_query(query.id)  # Delete the loading circle
    await query.message.edit_text(
        text=const.LOGOUT_MESSAGE,
        reply_markup=markup.get_logout_markup()
    )


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


async def back(client, query):
    user = await get_user_instance(query.from_user.id)
    user.restore_state()
    update_user(user)
    dump_users()

    await client.answer_callback_query(query.id)  # Delete the loading circle
    await query.message.edit_text(
        text=const.START_MESSAGE,
        reply_markup=markup.get_start_markup(user.session_key)
    )


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

    with ZipFile(history_zip) as zip:
        endsongs = list(filter(lambda x: ('MyData/endsong' in x), zip.namelist()))
        for item in endsongs:
            await update_history_loading_status(
                message=status,
                file_names=[message.document.file_name] + endsongs,
                step=step
            )
            with zip.open(item) as f:
                plays = json.loads(f.read().decode('utf-8'))
            user.store_plays(plays, registration_unixtime)
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


async def send_fire(client, query):
    _, user_receiver_id, track, artists = re.split(r'/@/', query.data)
    user_sender = await get_user_instance(query.from_user.id)
    user_receiver = await get_user_instance(user_receiver_id)

    if user_sender.id == user_receiver.id:
        return await client.answer_callback_query(
            query.id,
            const.AUTOFIRE
        )

    is_added = user_sender.toggle_fire_sending(user_receiver.id, artists, track)
    user_receiver.toggle_fire_addition(user_sender.id, artists, track)
    update_user(user_sender)
    update_user(user_receiver)
    dump_users()

    await query.message.edit_reply_markup(
        reply_markup=markup.get_mood_markup(
            user_receiver.id,
            user_receiver.get_track_fires(artists, track),
            track[:const.CALLBACK_DATA_MAX],
            artists[:const.CALLBACK_DATA_MAX]
        )
    )
    await client.answer_callback_query(
        query.id, 
        const.FIRE_ADDED if is_added else const.FIRE_REMOVED
    )
