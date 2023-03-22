from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import const


def get_start_markup(user):
    if user['session_key']:
        text = const.LOGGED_BUTTON
        callback_data = 'logout'
    else:
        text = const.NOT_LOGGED_BUTTON
        callback_data = 'login'

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text=text, callback_data=callback_data)]
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
