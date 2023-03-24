from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import const


def get_start_markup(user):
    if user['session_key']:
        text = const.LOGOUT_BUTTON
        auth_callback_data = 'logout'
    else:
        text = const.LOGIN_BUTTON
        auth_callback_data = 'login'

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text=text, callback_data=auth_callback_data)],
        [InlineKeyboardButton(text=const.SETTINGS_BUTTON, callback_data='settings')],
        [
            InlineKeyboardButton(text=const.CHANNEL_BUTTON, url=const.CHANNEL_LINK),
            InlineKeyboardButton(text=const.SOURCE_BUTTON, url=const.SOURCE_LINK)
        ]
    ])


def get_login_markup(auth_url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text=const.AUTH_BUTTON, url=auth_url)],
        [InlineKeyboardButton(text=const.DONE_BUTTON, callback_data='auth_done')], 
        [InlineKeyboardButton(text=const.BACK_BUTTON, callback_data='back')]
    ])


def get_logout_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text=const.UNAUTH_BUTTON, callback_data='unauth_done')],
        [InlineKeyboardButton(text=const.BACK_BUTTON, callback_data='back')]
    ])

def get_settings_markup(auth_url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text=const.LOAD_HISTORY_BUTTON, callback_data='load_history')]
    ])
