import os
import configparser

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG_FILE_NAME = f'{PROJECT_ROOT}/src/config.ini'
USER_SETTINGS_PATH = f'{PROJECT_ROOT}/src/user_settings.json'
config = configparser.ConfigParser()
config.read(CONFIG_FILE_NAME)

TG_API_ID = config['telegram']['api_id']
TG_API_HASH = config['telegram']['api_hash']
BOT_TOKEN = config['telegram']['bot_token']
BOT_USERNAME = config['telegram']['bot_username']
FM_API_KEY = config['last_fm']['api_key']
FM_API_SECRET = config['last_fm']['api_secret']
SESSION_NAME = config['misc']['session_name']

CACHE_TIME = 3

HEADPHONES = '\U0001F3A7'
TOOL = '\U0001F6E0'
TIC = '\u2705'
GREY_TIC = '\u2611' + '\uFE0F'
CROSS = '\u274C'
GLOBE = '\U0001F310'
PADLOCK_KEY = '\U0001F510'
PADLOCK = '\U0001F512'
BACK = '\U0001F519'
MEGAPHONE = '\U0001F4E3'
PEOPLE = '\U0001F465'

CHANNEL_LINK = 't.me/MOODFM_CHANNEL'
SOURCE_LINK = 'github.com/alessiocelentano/MOOD-FM'

START_MESSAGE = f'''{HEADPHONES} <b><u>What is MOOD-FM?</u></b>
MOOD-FM is a detailed LastFM interface on Telegram with several additional features. \
Share your music in chats in a quick way.\n
{TOOL} <b>Usage</b>
WiP\n
@alessiocelentano | <a href="{CHANNEL_LINK}">Follow us</a> | <a href="{SOURCE_LINK}">GitHub</a>
'''

LOGIN_MESSAGE = f'''{PEOPLE} <b><u>Connect with us</u></b>
Authorize MOOD-FM to access your scrobbles.
Once logged in, click on "Done" button
'''

LOGOUT_MESSAGE = f'''{CROSS} <b><u>Unauthorize</u></b>
You\'re currently logged in with your Last FM account.
Press the button below to unauthorize it
'''

AUTH_SUCCESS = f'{TIC} MOOD-FM authorizated successfully!'
UNAUTH_SUCCESS = f'{TIC} MOOD-FM unauthorizated successfully!'
LOGOUT_BUTTON =f'{CROSS} LOGOUT'
LOGIN_BUTTON = f'{GREY_TIC} LOGIN'
AUTH_BUTTON = f'{PADLOCK_KEY} AUTHORIZE'
UNAUTH_BUTTON = f'{PADLOCK} UNAUTHORIZE'
DONE_BUTTON = f'{TIC} DONE'
AUTH_ERROR = 'Error during authorization. Try again'
BACK_BUTTON = f'{BACK} BACK'
CHANNEL_BUTTON = f'{MEGAPHONE} CHANNEL'
SOURCE_BUTTON = f'{GLOBE} SOURCE'
