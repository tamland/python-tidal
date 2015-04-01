# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
import json
import logging
import requests
from collections import namedtuple
from .compat import urljoin
from .models import Artist, Album, Track, Playlist, SearchResult, Category

log = logging.getLogger(__name__)

Api = namedtuple('API', ['location', 'token'])

WIMP_API = Api(
    location='https://play.wimpmusic.com/v1/',
    token='oIaGpqT_vQPnTr0Q',
)

TIDAL_API = Api(
    location='https://listen.tidalhifi.com/v1/',
    token='P5Xbeo5LFvESeDy6',
)


class Quality(object):
    lossless = 'LOSSLESS'
    high = 'HIGH'
    low = 'LOW'


class Config(object):
    api = WIMP_API
    """:type api: :class:`Api`"""
    quality = Quality.high

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Session(object):

    def __init__(self, config=Config()):
        self.session_id = None
        self.country_code = None
        self.user = None
        self._config = config
        """:type _config: :class:`Config`"""

    def load_session(self, session_id, country_code, user_id):
        self.session_id = session_id
        self.country_code = country_code
        self.user = User(self, id=user_id)

    def login(self, username, password):
        url = urljoin(self._config.api.location, 'login/username')
        params = {'token': self._config.api.token}
        payload = {
            'username': username,
            'password': password,
        }
        r = requests.post(url, data=payload, params=params)
        r.raise_for_status()
        body = r.json()
        self.session_id = body['sessionId']
        self.country_code = body['countryCode']
        self.user = User(self, id=body['userId'])
        return True

    def check_login(self):
        """ Returns true if current session is valid, false otherwise. """
        if self.user is None or not self.user.id or not self.session_id:
            return False
        url = urljoin(self._config.api.location, 'users/%s/subscription' % self.user.id)
        return requests.get(url, params={'sessionId': self.session_id}).ok

    def request(self, method, path, params=None, data=None):
        request_params = {
            'sessionId': self.session_id,
            'countryCode': self.country_code,
            'limit': '9999',
        }
        if params:
            request_params.update(params)
        url = urljoin(self._config.api.location, path)
        r = requests.request(method, url, params=request_params, data=data)
        log.debug("request: %s" % r.request.url)
        r.raise_for_status()
        if r.content:
            log.debug("response: %s" % json.dumps(r.json(), indent=4))
        return r

    def get_user(self, user_id):
        return self._map_request('users/%s' % user_id, ret='user')

    def get_user_playlists(self, user_id):
        return self._map_request('users/%s/playlists' % user_id, ret='playlists')

    def get_playlist(self, playlist_id):
        return self._map_request('playlists/%s' % playlist_id, ret='playlist')

    def get_playlist_tracks(self, playlist_id):
        return self._map_request('playlists/%s/tracks' % playlist_id, ret='tracks')

    def get_album(self, album_id):
        return self._map_request('albums/%s' % album_id, ret='album')

    def get_album_tracks(self, album_id):
        return self._map_request('albums/%s/tracks' % album_id, ret='tracks')

    def get_artist(self, artist_id):
        return self._map_request('artists/%s' % artist_id, ret='artist')

    def get_artist_albums(self, artist_id):
        return self._map_request('artists/%s/albums' % artist_id, ret='albums')

    def get_artist_albums_ep_singles(self, artist_id):
        params = {'filter': 'EPSANDSINGLES'}
        return self._map_request('artists/%s/albums' % artist_id, params, ret='albums')

    def get_artist_albums_other(self, artist_id):
        params = {'filter': 'COMPILATIONS'}
        return self._map_request('artists/%s/albums' % artist_id, params, ret='albums')

    def get_artist_top_tracks(self, artist_id):
        return self._map_request('artists/%s/toptracks' % artist_id, ret='tracks')

    def get_artist_bio(self, artist_id):
        return self.request('GET', 'artists/%s/bio' % artist_id).json()['text']

    def get_artist_similar(self, artist_id):
        return self._map_request('artists/%s/similar' % artist_id, ret='artists')

    def get_artist_radio(self, artist_id):
        return self._map_request('artists/%s/radio' % artist_id, params={'limit': 100}, ret='tracks')

    def get_featured(self):
        items = self.request('GET', 'promotions').json()['items']
        return [_parse_featured_playlist(item) for item in items if item['type'] == 'PLAYLIST']

    def get_featured_items(self, content_type, group):
        return self._map_request('/'.join(['featured', group, content_type]), ret=content_type)

    def get_moods(self):
        return map(_parse_moods, self.request('GET', 'moods').json())

    def get_mood_playlists(self, mood_id):
        return self._map_request('/'.join(['moods', mood_id, 'playlists']), ret='playlists')

    def get_genres(self):
        return map(_parse_genres, self.request('GET', 'genres').json())

    def get_genre_items(self, genre_id, content_type):
        return self._map_request('/'.join(['genres', genre_id, content_type]), ret=content_type)

    def get_track_radio(self, track_id):
        return self._map_request('tracks/%s/radio' % track_id, params={'limit': 100}, ret='tracks')

    def _map_request(self, url, params=None, ret=None):
        json_obj = self.request('GET', url, params).json()
        parse = None
        if ret.startswith('artist'):
            parse = _parse_artist
        elif ret.startswith('album'):
            parse = _parse_album
        elif ret.startswith('track'):
            parse = _parse_track
        elif ret.startswith('user'):
            raise NotImplementedError()
        elif ret.startswith('playlist'):
            parse = _parse_playlist

        items = json_obj.get('items')
        if items is None:
            return parse(json_obj)
        elif len(items) > 0 and 'item' in items[0]:
            return list(map(parse, [item['item'] for item in items]))
        else:
            return list(map(parse, items))

    def get_media_url(self, track_id):
        params = {'soundQuality': self._config.quality}
        r = self.request('GET', 'tracks/%s/streamUrl' % track_id, params)
        return r.json()['url']

    def search(self, field, value):
        params = {
            'query': value,
            'limit': 50,
        }
        if field not in ['artist', 'album', 'playlist', 'track']:
            raise ValueError('Unknown field \'%s\'' % field)

        ret_type = field + 's'
        url = 'search/' + field + 's'
        result = self._map_request(url, params, ret=ret_type)
        return SearchResult(**{ret_type: result})


def _parse_artist(json_obj):
    return Artist(id=json_obj['id'], name=json_obj['name'])


def _parse_album(json_obj, artist=None):
    if artist is None:
        artist = _parse_artist(json_obj['artist'])
    kwargs = {
        'id': json_obj['id'],
        'name': json_obj['title'],
        'num_tracks': json_obj.get('numberOfTracks'),
        'duration': json_obj.get('duration'),
        'artist': artist,
    }
    return Album(**kwargs)


def _parse_featured_playlist(json_obj):
    kwargs = {
        'id': json_obj['artifactId'],
        'name': json_obj['header'],
        'description': json_obj['text'],
    }
    return Playlist(**kwargs)


def _parse_playlist(json_obj):
    kwargs = {
        'id': json_obj['uuid'],
        'name': json_obj['title'],
        'description': json_obj['description'],
        'num_tracks': int(json_obj['numberOfTracks']),
        'duration': int(json_obj['duration']),
        'is_public': json_obj['publicPlaylist'],
        #TODO 'creator': _parse_user(json_obj['creator']),
    }
    return Playlist(**kwargs)


def _parse_track(json_obj):
    artist = _parse_artist(json_obj['artist'])
    album = _parse_album(json_obj['album'], artist)
    kwargs = {
        'id': json_obj['id'],
        'name': json_obj['title'],
        'duration': json_obj['duration'],
        'track_num': json_obj['trackNumber'],
        'disc_num': json_obj['volumeNumber'],
        'popularity': json_obj['popularity'],
        'artist': artist,
        'album': album,
        'available': bool(json_obj['streamReady']),
    }
    return Track(**kwargs)


def _parse_genres(json_obj):
    image = "http://resources.wimpmusic.com/images/%s/460x306.jpg" \
            % json_obj['image'].replace('-', '/')
    return Category(id=json_obj['path'], name=json_obj['name'], image=image)


def _parse_moods(json_obj):
    image = "http://resources.wimpmusic.com/images/%s/342x342.jpg" \
            % json_obj['image'].replace('-', '/')
    return Category(id=json_obj['path'], name=json_obj['name'], image=image)


class Favorites(object):

    def __init__(self, session, user_id):
        self._session = session
        self._base_url = 'users/%s/favorites' % user_id

    def add_artist(self, artist_id):
        return self._session.request('POST', self._base_url + '/artists', data={'artistId': artist_id}).ok

    def add_album(self, album_id):
        return self._session.request('POST', self._base_url + '/albums', data={'albumId': album_id}).ok

    def add_track(self, track_id):
        return self._session.request('POST', self._base_url + '/tracks', data={'trackId': track_id}).ok

    def remove_artist(self, artist_id):
        return self._session.request('DELETE', self._base_url + '/artists/%s' % artist_id).ok

    def remove_album(self, album_id):
        return self._session.request('DELETE', self._base_url + '/albums/%s' % album_id).ok

    def remove_track(self, track_id):
        return self._session.request('DELETE', self._base_url + '/tracks/%s' % track_id).ok

    def artists(self):
        return self._session._map_request(self._base_url + '/artists', ret='artists')

    def albums(self):
        return self._session._map_request(self._base_url + '/albums', ret='albums')

    def playlists(self):
        return self._session._map_request(self._base_url + '/playlists', ret='playlists')

    def tracks(self):
        r = self._session.request('GET', self._base_url + '/tracks')
        return [_parse_track(item['item']) for item in r.json()['items']]


class User(object):

    favorites = None

    def __init__(self, session, id):
        """
        :type session: :class:`wimpy.Session`
        :param id: The user ID
        """
        self._session = session
        self.id = id
        self.favorites = Favorites(session, self.id)

    def playlists(self):
        return self._session.get_user_playlists(self.id)
