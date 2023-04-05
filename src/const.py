import os
import configparser

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG_FILE_PATH = f'{PROJECT_ROOT}/src/config.ini'
USERS_PATH = f'{PROJECT_ROOT}/src/users.json'
CACHE_PATH = f'{PROJECT_ROOT}/src/cache.json'
FONT = f'{PROJECT_ROOT}/fonts/Roboto-Bold.ttf'
NO_COVER = f'{PROJECT_ROOT}/assets/no_cover.jpg'
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

TG_API_ID = config['telegram']['api_id']
TG_API_HASH = config['telegram']['api_hash']
BOT_TOKEN = config['telegram']['bot_token']
BOT_USERNAME = config['telegram']['bot_username']
FM_API_KEY = config['last_fm']['api_key']
FM_API_SECRET = config['last_fm']['api_secret']
SPOTIFY_CLIENT_ID = config['spotify']['client_id']
SPOTIFY_CLIENT_SECRET = config['spotify']['client_secret']
SESSION_NAME = config['misc']['session_name']

CACHE_TIME = 3
PLAY_MINIMUM_MS = 30000
CALLBACK_DATA_MAX = 20
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DEFAULT_COLLAGE_COLUMNS = 3
DEFAULT_COLLAGE_ROWS = 3
SEVEN_DAYS_IN_SECONDS = 604800
ONE_MONTH_IN_SECONDS = 2592000
THREE_MONTHS_IN_SECONDS = 7776000
SIX_MONTHS_IN_SECONDS = 15552000
TWELVE_MONTHS_IN_SECONDS = 31536000
BROADCASTER_ID = 312012637

TRACK = 'track'
ARTIST = 'artist'
ALBUM = 'album'

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
MAGNIFYING_GLASS = '\U0001F50E'
PARTY_POPPER = '\U0001F389'
FIRE = '\U0001F525'
WARNING = '\u26A0'
NOTE = '\U0001F3B5'
DISK = '\U0001F4BF'
PERSON = '\U0001F464'
TIME = '\U0001F551'
GLOWING_STAR = '\U0001F31F'
REPEAT_ONE = '\U0001F502'

CHANNEL_LINK = 't.me/MOODFM_CHANNEL'
SOURCE_LINK = 'github.com/alessiocelentano/MOOD-FM'
TUTORIAL_LINK = 'https://telegra.ph/MOOD-FM-TUTORIAL-03-26'

START_MESSAGE = f'''<a href="{TUTORIAL_LINK}">{HEADPHONES}</a> <b><u>What is MOOD-FM?</u></b>
MOOD-FM is a detailed LastFM interface on Telegram with several additional features. \
Share your music in chats in a quick way.\n
{TOOL} <b><u>Usage</u></b>
Use the command /mood in any chat with MOOD-FM.\n
@alessiocelentano | <a href="{CHANNEL_LINK}">Follow us</a> | <a href="{SOURCE_LINK}">GitHub</a>
'''

LOGIN_MESSAGE = f'''{PEOPLE} <b><u>Connect with us</u></b>
Authorize MOOD-FM to access your plays.
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
LastFM starts to keep track of your plays when you join it.
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

STATUS_HISTORY_LOAD_MESSAGE = OUTBOX + ''' <b>Loading history. It may take a few seconds</b>\n
{1} Download of <code>{0}</code>
'''

HISTORY_LOADED_MESSAGE = f'{PARTY_POPPER} History loaded successfully'

MOOD_MESSAGE = '''{fire_emoji} <b>{fires_received}</b> ➠ <i><a href="{user_url}">{user_firstname}</a> is listening to:</i>\n
<b>{loved_song_emoji}{track} • {headphones_emoji} {plays}</b>
╰┈➤ <i>by {artists}</i>
'''

PLAYS_IN_A_ROW = '{} <b><u>{} plays in a row!</u></b>'

COLLAGE_MESSAGE = '''<b><u><a href="{user_link}">{first_name}</a>\'s {size[0]}x{size[1]} collage</u>
╰┈➤ {type_emoji} {type}s
╰┈➤ {time_emoji} {time}</b>
'''

LOADING_COLLAGE_MESSAGE = f'''{HOURGLASS} <i>Collage creation in progress...
It may take a while</i>
'''

MOOD_ERROR = '{cross_emoji} <i>{user_firstname}</i>, you are not currently listening to any tracks'

COLLAGE_ERROR = f'''<a href="{TUTORIAL_LINK}">{CROSS}</a> Error: invalid use of the command.
Please check out the tutorial to see the parameters available for /collage
'''

COLLAGE_ARGS_WARNING = f'<i>\n{WARNING} One or more parameters are invalid. Please check the !collage usage on the <a href="{TUTORIAL_LINK}">tutorial</a></i>'

AUTH_SUCCESS = f'{TIC} MOOD-FM authorizated successfully!'
UNAUTH_SUCCESS = f'{TIC} MOOD-FM unauthorizated successfully!'
ALREADY_LOADED = 'You already loaded your history'
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
FIRE_ADDED = f'{FIRE} +1 Fire'
FIRE_REMOVED = 'Fire removed'
AUTOFIRE = f'{CROSS} Cannot auto-Fire'
