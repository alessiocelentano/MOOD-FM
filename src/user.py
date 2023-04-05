from time import time

from pylast import PERIOD_7DAYS, PERIOD_1MONTH, PERIOD_3MONTHS, \
                PERIOD_6MONTHS, PERIOD_12MONTHS, PERIOD_OVERALL

from const import SEVEN_DAYS_IN_SECONDS, ONE_MONTH_IN_SECONDS, \
                THREE_MONTHS_IN_SECONDS, SIX_MONTHS_IN_SECONDS, TWELVE_MONTHS_IN_SECONDS
import const
from pylast import WSError


class User():
    def __init__(self, id, name=None, session_key=None, session_key_generator=None,
                auth_url=None, is_history_loaded=False, is_loading_files=False,
                fires_received=[], fires_sended=[], plays_before_lastfm=[]):
        self.id = id
        self.name = name
        self.session_key = session_key
        self.session_key_generator = session_key_generator
        self.auth_url = auth_url
        self.is_history_loaded = is_history_loaded
        self.is_loading_files = is_loading_files
        self.fires_received = fires_received
        self.fires_sended = fires_sended
        self.plays_before_lastfm = plays_before_lastfm


    @property
    def fires(self):
        return len(self.fires_received)


    def store_plays(self, plays, registration_unixtime):
        for p in plays:
            if p['ms_played'] < const.PLAY_MINIMUM_MS:
                continue

            play_unixtime = self._timestamp_to_unixtime(p['ts'])
            if play_unixtime > registration_unixtime:
                continue

            artist = p['master_metadata_album_artist_name']
            track = p['master_metadata_track_name']
            album = p['master_metadata_album_album_name']
            indexes = self._find_item_indexes(const.TRACK, artist=artist, track=track)

            if not indexes:
                self._create_track(artist, track, album, play_unixtime)
            else:
                self._add_play_to_track(indexes.pop(), play_unixtime)


    def find_tracks(self, type, artist=None, track=None, album=None):
        matches = []
        for i in self._find_item_indexes(type, artist=artist, track=track, album=album):
            matches.append(self.plays_before_lastfm[i])
        return matches


    def get_history_items(self, time_range, type):
        items = {}
        for tr in self.plays_before_lastfm:
            key = self._create_key_dict_from_item(type, tr['artist'], tr[type])
            for pl in tr['plays_unixtime']:
                if not self._is_within_time_range(pl, time_range):
                    continue
                if key in items:
                    items[key]['plays'] += 1
                else:
                    items[key] = {
                        'type': type,
                        'name': tr[type],
                        'artist': tr['artist'] if type != const.ARTIST else None,
                        'plays': 1,
                        'updated': False
                    }
        return items


    def _create_key_dict_from_item(self, type, artist, name):
        if type == const.TRACK:
            return f'{artist} - {name}'
        if type == const.ALBUM:
            return f'{artist} - {name}'
        if type == const.ARTIST:
            return artist

                
    def _is_within_time_range(self, unixtime, time_range):
        if time_range == PERIOD_7DAYS and time() - unixtime < SEVEN_DAYS_IN_SECONDS:
            return True
        elif time_range == PERIOD_1MONTH and time() - unixtime < ONE_MONTH_IN_SECONDS:
            return True
        elif time_range == PERIOD_3MONTHS and time() - unixtime < THREE_MONTHS_IN_SECONDS:
            return True
        elif time_range == PERIOD_6MONTHS and time() - unixtime < SIX_MONTHS_IN_SECONDS:
            return True
        elif time_range == PERIOD_12MONTHS and time() - unixtime < TWELVE_MONTHS_IN_SECONDS:
            return True
        elif time_range == PERIOD_OVERALL:
            return True
        return False


    def _find_item_indexes(self, type, artist=None, track=None, album=None):
        indexes = []
        for i, item in enumerate(self.plays_before_lastfm):
            if type == const.TRACK:
                if track == item['track'] and artist == item['artist']:
                    return [i]
            elif type == const.ALBUM:
                if album == item['album'] and artist == item['artist']:
                    indexes.append(i)
            elif type == const.ARTIST:
                if artist == i['artist']:
                    indexes.append(i)
        return indexes


    def _timestamp_to_unixtime(self, timestamp):
        timestamp_obj = time.strptime(timestamp, const.DATETIME_FORMAT)
        return int(time.mktime(timestamp_obj))


    def _create_track(self, artist, track, album, play_unixtime):
        self.plays_before_lastfm.append({
            'artist': artist, 
            'track': track,
            'album': album,
            'plays': 1,
            'plays_unixtime': [play_unixtime]
        })


    def _add_play_to_track(self, index, play_unixtime):
        self.plays_before_lastfm[index]['plays'] += 1
        self.plays_before_lastfm[index]['plays_unixtime'].append(play_unixtime)


    def toggle_fire_addition(self, user_sender_id, artist, track):
        for index, fire in enumerate(self.fires_received):
            if fire['artist'] != artist:
                continue
            if fire['track'] != track:
                continue
            if fire['user'] != user_sender_id:
                continue
            del self.fires_received[index]
            return False

        self.fires_received.append({
            'artist': artist, 
            'track': track,
            'user': user_sender_id
        })
        return True


    def toggle_fire_sending(self, user_receiver_id, artist, track):
        for index, fire in enumerate(self.fires_sended):
            if fire['artist'] != artist:
                continue
            if fire['track'] != track:
                continue
            if fire['user'] != user_receiver_id:
                continue
            del self.fires_sended[index]
            return False

        self.fires_sended.append({
            'artist': artist, 
            'track': track,
            'user': user_receiver_id
        })
        return True


    def get_track_fires(self, artist, track):
        counter = 0
        for f in self.fires_received:
            if f['artist'] != artist[:const.CALLBACK_DATA_MAX]:
                continue
            if f['track'] != track[:const.CALLBACK_DATA_MAX]:
                continue
            counter += 1
        return counter


    def get_playcount(self, playing_track):
        try:
            lastfm_playcount = playing_track.get_userplaycount()
        except WSError:
            # It seems that get_userplaycount() can't be called when a track is too recent
            lastfm_playcount = 0

        artist = playing_track.artist.name
        track = playing_track.title

        for item in self.plays_before_lastfm:
            if item['artist'] and artist in item['artist'] and item['track'] == track:
                return lastfm_playcount + item['plays']

        return lastfm_playcount


    def restore_state(self):
        if self.is_loading_files or self.session_key_generator:
            self.is_loading_files = False
            self.session_key_generator = None
            self.auth_url = None
