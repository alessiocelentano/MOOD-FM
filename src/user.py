import time
import json

import const


class User():
    def __init__(self, id, name=None, session_key=None,
                session_key_generator=None, auth_url=None,
                is_history_loaded=False, is_loading_files=False,
                scrobbles_before_lastfm=[]):
        self.id = id
        self.name = name
        self.session_key = session_key
        self.is_history_loaded = is_history_loaded
        self.is_loading_files = is_loading_files
        self.scrobbles_before_lastfm = scrobbles_before_lastfm
        self.session_key_generator = session_key_generator
        self.auth_url = auth_url

    def store_scrobbles(self, scrobbles, registration_unixtime):
        for scr in scrobbles:
            if scr['ms_played'] < const.SCROBBLE_MINIMUM_MS:
                continue

            scrobble_unixtime = self._timestamp_to_unixtime(scr['ts'])
            if scrobble_unixtime > registration_unixtime:
                continue

            artist = scr['master_metadata_album_artist_name']
            track_name = scr['master_metadata_track_name']
            album = scr['master_metadata_album_album_name']
            index = self._find_track(artist, track_name)

            if index:
                self.scrobbles_before_lastfm[index]['scrobbles'] += 1
                self._update_firstlisten_unixtime(scrobble_unixtime, index)
            else:
                self._add_track(artist, track_name, album, scrobble_unixtime)


    def _timestamp_to_unixtime(self, timestamp):
        timestamp_obj = time.strptime(timestamp, const.DATETIME_FORMAT)
        return int(time.mktime(timestamp_obj))


    def _find_track(self, artist, track_name):
        for i, item in enumerate(self.scrobbles_before_lastfm):
            if item['artist'] == artist and item['track_name'] == track_name:
                return i
        return None


    def _update_firstlisten_unixtime(self, scrobble_unixtime, index):
        if scrobble_unixtime < self.scrobbles_before_lastfm[index]['unixtime_firstlisten']:
            self.scrobbles_before_lastfm[index]['unixtime_firstlisten'] = scrobble_unixtime


    def _add_track(self, artist, track_name, album, scrobble_unixtime):
        self.scrobbles_before_lastfm.append({
            'artist': artist, 
            'track_name': track_name,
            'album': album,
            'scrobbles': 1,
            'unixtime_firstlisten': scrobble_unixtime
        })