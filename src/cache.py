import json

import const


with open(const.USERS_PATH) as f:
    users_list = json.load(f)
with open(const.CACHE_PATH) as f:
    cache = json.load(f)


def update_user(user):
    # id is stored as string because json.dump() would generate
    # duplicate if we use int, since it would eventually converted in a string
    users_list[str(user.id)] = {
        'id': user.id,
        'name': user.name,
        'session_key': user.session_key,
        'session_key_generator': user.session_key_generator,
        'auth_url': user.auth_url,
        'is_history_loaded': user.is_history_loaded,
        'is_loading_files': user.is_loading_files, 
        'fires_received': user.fires_received,
        'fires_sended': user.fires_sended,
        'scrobbles_before_lastfm': user.scrobbles_before_lastfm
    }

def update_cache(key, value):
    cache[key] = value


def dump_users():
    with open(const.USERS_PATH, 'w+') as f:
        json.dump(users_list, f, indent=4)


def dump_cache():
    with open(const.CACHE_PATH, 'w+') as f:
        json.dump(cache, f, indent=4)
