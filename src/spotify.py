import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from cache import cache, update_cache, dump_cache
from const import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, TRACK


spotify = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)


def get_spotify_track_infos(track):
    query = ' '.join([track.title, track.artist.name])
    if query in cache:
        return list(cache[query].values())
    track_infos = get_search_result(query, TRACK)
    track = get_track(track_infos)
    artists = get_artists(track_infos['artists'])
    cover_url = get_cover_url(track_infos, TRACK)
    track_value = {
        'track': track,
        'artists': artists,
        'image_url': cover_url
    }
    update_cache(query, track_value)
    dump_cache()
    return tuple(track_value.values())


def get_name(track_infos):
    return track_infos['name']


def get_artists(artists_info):
    return ', '.join([artist['name'] for artist in artists_info])


def get_cover_url(item_infos, type):
    if type == TRACK:
        item_infos = item_infos['album']
    if not item_infos['images']:
        return None
    return item_infos['images'][0]['url']


def get_search_result(query, type, limit=1):
    search = spotify.search(
        q=query,
        limit=limit,
        type=type
    )
    return search[f'{type}s']['items'].pop()
