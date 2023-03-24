import os
import configparser

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG_FILE_PATH = f'{PROJECT_ROOT}/src/config.ini'
USER_SETTINGS_PATH = f'{PROJECT_ROOT}/src/user_settings.json'
HISTORY_PATH = f'{PROJECT_ROOT}/histories/'
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

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
WRENCH = '\U0001F6E0'
OUTBOX = '\U0001F4E4'
QUESTION_MARK = '\u2753'
RADIO_BUTTON = '\U0001F518'
HOURGLASS = '\u23F3'

CHANNEL_LINK = 't.me/MOODFM_CHANNEL'
SOURCE_LINK = 'github.com/alessiocelentano/MOOD-FM'

START_MESSAGE = f'''{HEADPHONES} <b><u>What is MOOD-FM?</u></b>
MOOD-FM is a detailed LastFM interface on Telegram with several additional features. \
Share your music in chats in a quick way.\n
{TOOL} <b><u>Usage</u></b>
Use the command /now in any chat with MOOD-FM.
Check out /help for a full list of commands\n
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

SETTINGS_MESSAGE = '''{} <b><u>Settings</u></b>\n
<b>Spotify history loaded:</b> {}
'''

LOAD_HISTORY_MESSAGE = f'''{OUTBOX} <b><u>Load history</u></b>
LastFM starts to keep track of your scrobbles when you join it.
On MOOD-FM you can load your Spotify history to update your data.
Send your <code>my_spotify_data.zip</code> here

{QUESTION_MARK} <b>How can I get my history?</b>
You can request your history at <a href="https://www.spotify.com/us/account/privacy/">this link</a> \
checking the "Extended streaming history" box
'''

NOT_LOGGED_MESSAGE = f'''{CROSS} Cannot use this feature. Authentication required
'''

INVALID_HISTORY_MESSAGE = f'''{CROSS} Invalid type of file. Try again
Send your <code>my_spotify_data.zip</code>
'''

STATUS_HISTORY_LOAD_MESSAGE = '''{1} Download of <code>{0}</code>
{2} Unzip of <code>{0}</code>
{3} Save history
'''

AUTH_SUCCESS = f'{TIC} MOOD-FM authorizated successfully!'
UNAUTH_SUCCESS = f'{TIC} MOOD-FM unauthorizated successfully!'
LOGOUT_BUTTON =f'{CROSS} LOGOUT'
LOGIN_BUTTON = f'{GREY_TIC} LOGIN'
AUTH_BUTTON = f'{PADLOCK_KEY} AUTHORIZE'
UNAUTH_BUTTON = f'{PADLOCK} UNAUTHORIZE'
DONE_BUTTON = f'{TIC} DONE'
AUTH_ERROR = f'{CROSS} Error during authorization. Try again'
BACK_BUTTON = f'{BACK} BACK'
CHANNEL_BUTTON = f'{MEGAPHONE} CHANNEL'
SOURCE_BUTTON = f'{GLOBE} SOURCE'
SETTINGS_BUTTON = f'{WRENCH} SETTINGS'
LOAD_HISTORY_BUTTON = f'{OUTBOX} LOAD HISTORY'
