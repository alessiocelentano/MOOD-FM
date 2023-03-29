import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import const


spotify = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=const.SPOTIFY_CLIENT_ID,
        client_secret=const.SPOTIFY_CLIENT_SECRET
    )
)


def get_spotify_track_infos(track):
    query = ' '.join([track.title, track.artist.name])
    track_infos = get_search_result(query, const.TRACK)
    track_name = get_track_name(track_infos)
    track_artists = get_artists(track_infos['artists'])
    track_cover_url = get_cover_url(track_infos, const.TRACK)
    return (track_name, track_artists, track_cover_url)


def get_track_name(track_infos):
    return track_infos['name']


def get_artists(artists_info):
    return ', '.join([artist['name'] for artist in artists_info])


def get_cover_url(item_infos, type):
    if type == const.TRACK:
        return item_infos['album']['images'][0]['url']
    if type == const.ARTIST or type == const.ALBUM:
        return item_infos['images'][0]['url']


def get_search_result(query, type):
    return spotify.search(query, limit=1, type=type)[f'{type}s']['items'][0]
