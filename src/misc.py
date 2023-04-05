import re

from pylast import PERIOD_7DAYS, PERIOD_1MONTH, PERIOD_3MONTHS, \
                PERIOD_6MONTHS, PERIOD_12MONTHS, PERIOD_OVERALL

from cache import users_list, update_user, dump_users
import const
from user import User



def get_size(text):
    size_match = re.search(r'\s([1-9]|10)x\1(?=\s|$)', text)
    if size_match:
        return tuple(int(group) for group in re.split(r'x', size_match.group(0)))
    return None


def get_time_range(text):
    if re.search(r'\s(7d(ays)?)|(1w(eek)?)(?=\s|$)', text):
        return PERIOD_7DAYS
    if re.search(r'\s1m(onths)?(?=\s|$)', text):
        return PERIOD_1MONTH
    if re.search(r'\s3m(onths)?(?=\s|$)', text):
        return PERIOD_3MONTHS
    if re.search(r'\s6m(onths)?(?=\s|$)', text):
        return PERIOD_6MONTHS
    if re.search(r'\s(12m(onths)?)|(1y(ear)?)(?=\s|$)', text):
        return PERIOD_12MONTHS
    if re.search(r'\s(overall)|(all(time)?)(?=\s|$)', text):
        return PERIOD_OVERALL
    return None


def get_top_type(text):
    if re.search(r'\sar(tist(s)?)?(?=\s|$)', text):
        return const.ARTIST
    if re.search(r'\sal(bum(s)?)?(?=\s|$)', text):
        return const.ALBUM
    if re.search(r'\str(ack(s)?)?(?=\s|$)', text):
        return const.TRACK
    return None


def get_type_emoji(type):
    if type == const.TRACK:
        return const.NOTE 
    if type == const.ALBUM:
        return const.DISK
    if type == const.ARTIST:
        return const.PERSON


def prettify_time_range(time_range):
    if time_range == PERIOD_7DAYS:
        return 'Last 7 days'
    if time_range == PERIOD_1MONTH:
        return 'Last month'
    if time_range == PERIOD_3MONTHS:
        return 'Last 3 months'
    if time_range == PERIOD_6MONTHS:
        return 'Last 6 months'
    if time_range == PERIOD_12MONTHS:
        return 'Last year'
    if time_range == PERIOD_OVERALL:
        return 'Overall'


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
