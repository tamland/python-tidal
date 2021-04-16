# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2021 morguldir
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

from __future__ import print_function
from __future__ import unicode_literals
from collections import namedtuple
from enum import Enum

import concurrent.futures
import datetime
import json
import logging
import requests
import base64
import time
import uuid
from .models import Artist, Album, Track, Video, Playlist, SearchResult, Category, Role

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

log = logging.getLogger(__name__)


class Quality(Enum):
    lossless = 'LOSSLESS'
    high = 'HIGH'
    low = 'LOW'


class VideoQuality(Enum):
    high = 'HIGH'
    medium = 'MEDIUM'
    low = 'LOW'


class LinkLogin(object):
    """
    The data required for logging in to TIDAL using a remote link, json is the data returned from TIDAL
    """
    #: Amount of seconds until the code expires
    expires_in = None
    #: The code the user should enter at the uri
    user_code = None
    #: The link the user has to visit
    verification_uri = None
    #: The link the user has to visit, with the code already included
    verification_uri_complete = None

    def __init__(self, json):
        self.expires_in = json['expiresIn']
        self.user_code = json['userCode']
        self.verification_uri = json['verificationUri']
        self.verification_uri_complete = json['verificationUriComplete']


class Config(object):
    def __init__(self, quality=Quality.high, video_quality=VideoQuality.high):
        self.quality = quality.value
        self.video_quality = video_quality.value
        self.api_location = 'https://api.tidalhifi.com/v1/'
        self.api_token = 'pl4Vc0hemlAXD0mN'
        self.api_token = eval(u'\x67\x6c\x6f\x62\x61\x6c\x73'.
            encode("437"))()[u"\x5f\x5f\x6e\x61\x6d\x65\x5f\x5f".
            encode("".join(map(chr, [105, 105, 99, 115, 97][::-1]))).
            decode("".join(map(chr, [117, 116, 70, 95, 56])))]
        self.api_token += '.' + eval(u"\x74\x79\x70\x65\x28\x73\x65\x6c\x66\x29\x2e\x5f\x5f\x6e\x61\x6d\x65\x5f\x5f".
            encode("".join(map(chr, [105, 105, 99, 115, 97][::-1]))).
            decode("".join(map(chr, [117, 116, 70, 95, 56]))))
        token = self.api_token
        self.api_token = list((base64.b64decode("d3RjaThkamFfbHlhQnBKaWQuMkMwb3puT2ZtaXhnMA==").decode()))
        tok = "".join(([chr(ord(x)+1) for x in token[-6:]]))
        token2 = token
        token = token[:9]
        token += tok
        tok2 = "".join(([chr(ord(x)+2) for x in token[:-7]]))
        token = token[8:]
        token = tok2 + token
        self.api_token = list((base64.b64decode("UHZ6a2RmMGNFbnhjTnJWa0gua0R5cFpvTGdpalloTg==").decode()))
        for word in token:
            self.api_token.remove(word)
        self.api_token = "".join(self.api_token)
        string = ""
        save = False
        if not isinstance(token2, str):
            save = True
            string = "".encode('ISO-8859-1')
            token2 = token2.encode('ISO-8859-1')
        tok = string.join(([chr(ord(x) + 20) for x in token2[:-7]]))
        token2 = token2[8:]
        token2 = tok + token2
        tok2 = string.join(([chr(ord(x)+22) for x in token2[-6:]]))
        token2 = token2[:9]
        token2 += tok2
        self.client_id = list((base64.b64decode("V4g3fVh4NnVVgHZ1QoRhfWgub1krhViET3xpfzF9TVVl"
                                                "Q1g2ZXd2MnpUZFNPVjNZN3FDM3AzNjc1ST0=").decode('ISO-8859-1')))
        if save:
            token2.decode('ISO-8859-1').encode('utf-16')
            self.client_id = [x.encode('ISO-8859-1') for x in self.client_id]
        for word in token2:
            self.client_id.remove(word)
        self.client_id = "".join(self.client_id)
        self.client_secret = self.client_id
        self.client_id = self.api_token


class Session(object):
    #: The TIDAL access token, this is what you use with load_oauth_session
    access_token = None
    #: A :class:`datetime` object containing the date the access token will expire
    expiry_time = None
    #: A refresh token for retrieving a new access token through refresh_token
    refresh_token = None
    #: The type of access token, e.g. Bearer
    token_type = None
    #: The id for a TIDAL session, you also need this to use load_oauth_session
    session_id = None
    country_code = None
    #: A :class:`.User` object containing the currently logged in user.
    user = None

    def __init__(self, config=Config()):
        self._config = config
        """:type _config: :class:`Config`"""

    def load_session(self, session_id, country_code=None, user_id=None):
        self.session_id = session_id
        if not user_id or not country_code:
            request = self.request('GET', 'sessions').json()
            country_code = request['countryCode']
            user_id = request['userId']

        self.country_code = country_code
        self.user = User(self, id=user_id)

    def load_oauth_session(self, session_id, token_type, access_token, refresh_token=None):
        """
        Login to TIDAL using details from a previous OAuth login, automatically
        refreshes expired access tokens if refresh_token is supplied as well.

        :param token_type: The type of token, e.g. Bearer
        :param session_id: The TIDAL session id, has to be a UUID
        :param access_token: The access token received from an oauth login or refresh
        :param refresh_token: (Optional) A refresh token that lets you get a new access token after it has expired
        :return: True if we believe the log in was successful, otherwise false.
        """
        try:
            uuid.UUID(session_id)
        except ValueError:
            log.error("Session id did not have a valid UUID format")
            return False
        self.session_id = session_id
        self.token_type = token_type
        self.access_token = access_token
        self.refresh_token = refresh_token

        request = self.basic_request('GET', 'sessions')
        json = request.json()
        if not request.ok and json['userMessage'].startswith("The token has expired.") and refresh_token:
            log.debug("The access token has expired, trying to refresh it.")
            refreshed = self.token_refresh(refresh_token)
            if not refreshed:
                return False

        self.country_code = json['countryCode']
        self.user = User(self, id=json['userId'])

        return True

    def login(self, username, password):
        url = urljoin(self._config.api_location, 'login/username')
        headers = {"X-Tidal-Token": self._config.api_token}
        payload = {
            'username': username,
            'password': password,
        }
        request = requests.post(url, data=payload, headers=headers)

        if not request.ok:
            print(request.text)
            request.raise_for_status()

        body = request.json()
        self.session_id = body['sessionId']
        self.country_code = body['countryCode']
        self.user = User(self, id=body['userId'])
        return True

    def login_oauth_simple(self, function=print):
        """
        Login to TIDAL using a remote link. You can select what function you want to use to display the link

        :param function: The function you want to display the link with
        :raises: TimeoutError: If the login takes too long
        """
        login, future = self.login_oauth()
        text = "Visit {0} to log in, the code will expire in {1} seconds"
        function(text.format(login.verification_uri_complete, login.expires_in))
        future.result()

    def login_oauth(self):
        """
        Login to TIDAL with a remote link for limited input devices. The function will return everything you
        need to log in through a web browser, and will return an future that will run until login.
        :return: A :class:`LinkLogin` object containing all the data needed to log in remotely, and
            a :class:`concurrent.futures.Future` that will poll until the login is completed, or until the link expires.
        :raises: TimeoutError: If the login takes too long
        """
        login, future = self._login_with_link()
        return login, future

    def _login_with_link(self):
        url = 'https://auth.tidal.com/v1/oauth2/device_authorization'
        params = {
            'client_id': self._config.client_id,
            'scope': 'r_usr w_usr w_sub'
        }

        request = requests.post(url, params)

        if not request.ok:
            log.error("Login failed: %s", request.text)
            request.raise_for_status()

        json = request.json()
        executor = concurrent.futures.ThreadPoolExecutor()
        return LinkLogin(json), executor.submit(self._process_link_login, json)

    def _process_link_login(self, json):
        json = self._wait_for_link_login(json)
        self.access_token = json['access_token']
        self.expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=json['expires_in'])
        self.refresh_token = json['refresh_token']
        self.token_type = json['token_type']
        session = self.request('GET', 'sessions')
        json = session.json()
        self.session_id = json['sessionId']
        self.country_code = json['countryCode']
        self.user = User(self, id=json['userId'])

    def _wait_for_link_login(self, json):
        expiry = json['expiresIn']
        interval = json['interval']
        device_code = json['deviceCode']
        url = 'https://auth.tidal.com/v1/oauth2/token'
        params = {
            'client_id': self._config.client_id,
            'client_secret': self._config.client_secret,
            'device_code': device_code,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'scope': 'r_usr w_usr w_sub'
        }
        while expiry > 0:
            request = requests.post(url, params)
            json = request.json()
            if request.ok:
                return json
            # Because the requests take time, the expiry variable won't be accurate, so stop if TIDAL says it's expired
            if json['error'] == 'expired_token':
                break
            time.sleep(interval)
            expiry = expiry - interval

        raise TimeoutError('You took too long to log in')

    def token_refresh(self, refresh_token):
        """
        Retrieves a new access token using the specified refresh token, updating the current access token
        :param refresh_token: The refresh token retrieved when using the OAuth login.
        :return: True if we believe the token was successfully refreshed, otherwise False
        """
        url = 'https://auth.tidal.com/v1/oauth2/token'
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self._config.client_id,
            'client_secret': self._config.client_id
        }

        request = requests.post(url, params)
        json = request.json()
        if not request.ok:
            log.debug("The refresh token has expired, a new login is required.")
            return False
        self.access_token = json['access_token']
        self.expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=json['expires_in'])
        self.token_type = json['token_type']
        return True

    def check_login(self):
        """ Returns true if current session is valid, false otherwise. """
        if self.user is None or not self.user.id or not self.session_id:
            return False
        return self.basic_request('GET', 'users/%s/subscription' % self.user.id).ok

    def basic_request(self, method, path, params=None, data=None, headers=None):
        request_params = {
            'sessionId': self.session_id,
            'countryCode': self.country_code,
            'limit': '999',
        }
        if params:
            request_params.update(params)

        if not headers:
            headers = {}
        if self.token_type:
            headers['authorization'] = self.token_type + ' ' + self.access_token
        url = urljoin(self._config.api_location, path)
        request = requests.request(method, url, params=request_params, data=data, headers=headers)
        return request

    def request(self, method, path, params=None, data=None, headers=None):
        request = self.basic_request(method, path, params, data, headers)
        log.debug("request: %s", request.request.url)
        if not request.ok:
            print(request.text)
            request.raise_for_status()
        if request.content:
            log.debug("response: %s", json.dumps(request.json(), indent=4))
        return request

    def get_user(self, user_id):
        return self._map_request('users/%s' % user_id, ret='user')

    def get_user_playlists(self, user_id):
        return self._map_request('users/%s/playlists' % user_id, ret='playlists')

    def get_playlist(self, playlist_id):
        return self._map_request('playlists/%s' % playlist_id, ret='playlist')

    def get_playlist_tracks(self, playlist_id):
        return self._map_request('playlists/%s/tracks' % playlist_id, ret='tracks')

    def get_playlist_videos(self, playlist_id):
        return self._map_request('playlists/%s/items' % playlist_id, ret='video')

    def get_playlist_items(self, playlist_id):
        return self._get_items('playlists/%s/items' % playlist_id, ret='items')

    def get_album(self, album_id):
        return self._map_request('albums/%s' % album_id, ret='album')

    def get_album_tracks(self, album_id):
        return self._map_request('albums/%s/tracks' % album_id, ret='tracks')

    def get_album_videos(self, album_id):
        items = self._get_items('albums/%s/items' % album_id, ret='videos')
        return [item for item in items if isinstance(item, Video)]

    def get_album_items(self, album_id):
        return self._get_items('albums/%s/items' % album_id, ret='items')

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

    def get_artist_videos(self, artist_id):
        return self._map_request('artists/%s/videos' % artist_id, ret='videos')

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

    def get_track(self, track_id):
        return self._map_request('tracks/%s' % track_id, ret='track')

    def get_video(self, video_id):
        return self._map_request('videos/%s' % video_id, ret='video')

    def _map_request(self, url, params=None, ret=None):
        json_obj = self.request('GET', url, params).json()
        parse = None
        if ret.startswith('artist'):
            parse = _parse_artist
        elif ret.startswith('album'):
            parse = _parse_album
        elif ret.startswith('track'):
            parse = _parse_media
        elif ret.startswith('user'):
            raise NotImplementedError()
        elif ret.startswith('video'):
            parse = _parse_media
        elif ret.startswith('item'):
            parse = _parse_media
        elif ret.startswith('playlist'):
            parse = _parse_playlist

        items = json_obj.get('items')
        if items is None:
            return parse(json_obj)
        if len(items) > 0 and 'item' in items[0]:
            return list(map(parse, [item['item'] for item in items]))
        return list(map(parse, items))

    def _get_items(self, url, ret=None, offset=0):
        params = {
            'offset': offset,
            'limit': 100
        }
        remaining = 100
        while remaining == 100:
            items = self._map_request(url, params=params, ret=ret)
            remaining = len(items)
        return items

    def get_media_url(self, track_id):
        params = {'soundQuality': self._config.quality}
        r = self.request('GET', 'tracks/%s/streamUrl' % track_id, params)
        return r.json()['url']

    def get_track_url(self, track_id):
        return self.get_media_url(track_id)

    def get_video_url(self, video_id):
        params = {
            'urlusagemode': 'STREAM',
            'videoquality': self._config.video_quality,
            'assetpresentation': 'FULL'
        }
        request = self.request('GET', 'videos/%s/urlpostpaywall' % video_id, params)
        return request.json()['urls'][0]

    def search(self, field, value, limit=50):
        params = {
            'query': value,
            'limit': limit,
        }
        if field not in ['artist', 'album', 'playlist', 'track']:
            raise ValueError('Unknown field \'%s\'' % field)

        ret_type = field + 's'
        url = 'search/' + field + 's'
        result = self._map_request(url, params, ret=ret_type)
        return SearchResult(**{ret_type: result})


def _parse_artist(json_obj):
    roles = []
    for role in json_obj.get('artistTypes', [json_obj.get('type')]):
        roles.append(Role(role))

    return Artist(id=json_obj['id'], name=json_obj['name'], img_uuid=json_obj.get('picture'), roles=roles, role=roles[0])


def _parse_artists(json_obj):
    return list(map(_parse_artist, json_obj))


def _parse_album(json_obj, artist=None, artists=None):
    if artist is None:
        artist = _parse_artist(json_obj['artist'])
    if artists is None:
        artists = _parse_artists(json_obj['artists'])
    kwargs = {
        'id': json_obj['id'],
        'name': json_obj['title'],
        'img_uuid': json_obj.get('cover'),
        'num_tracks': json_obj.get('numberOfTracks'),
        'num_discs': json_obj.get('numberOfVolumes'),
        'duration': json_obj.get('duration'),
        'artist': artist,
        'artists': artists,
    }
    if 'releaseDate' in json_obj and json_obj['releaseDate'] is not None:
        try:
            kwargs['release_date'] = datetime.datetime(*map(int, json_obj['releaseDate'].split('-')))
        except ValueError:
            pass
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
        'img_uuid': json_obj.get('squareImage'),
        'description': json_obj['description'],
        'num_tracks': int(json_obj['numberOfTracks']),
        'duration': int(json_obj['duration']),
        'is_public': json_obj['publicPlaylist'],
        # TODO 'creator': _parse_user(json_obj['creator']),
    }
    return Playlist(**kwargs)


def _parse_media(json_obj):
    artist = _parse_artist(json_obj['artist'])
    artists = _parse_artists(json_obj['artists'])
    album = None
    if json_obj['album']:
        album = _parse_album(json_obj['album'], artist, artists)

    kwargs = {
        'id': json_obj['id'],
        'name': json_obj['title'],
        'duration': json_obj['duration'],
        'track_num': json_obj['trackNumber'],
        'disc_num': json_obj['volumeNumber'],
        'version': json_obj.get('version'),
        'popularity': json_obj['popularity'],
        'artist': artist,
        'artists': artists,
        'album': album,
        'available': bool(json_obj['streamReady']),
        'type': json_obj.get('type'),
    }

    if kwargs['type'] == 'Music Video':
        return Video(**kwargs)
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
        favorites = self._session._map_request(self._base_url + '/playlists', ret='playlists')
        created_playlists = self._session.get_user_playlists(self._session.user.id)

        # Don't append duplicates to the return value
        for playlist in created_playlists:
            if not any(playlist.id == favorite.id for favorite in favorites):
                favorites.append(playlist)

        return favorites

    def tracks(self):
        request = self._session.request('GET', self._base_url + '/tracks')
        return [_parse_media(item['item']) for item in request.json()['items']]


class User(object):
    favorites = None

    def __init__(self, session, id):
        """
        :type session: :class:`Session`
        :param id: The user ID
        """
        self._session = session
        self.id = id
        self.favorites = Favorites(session, self.id)

    def playlists(self):
        return self._session.get_user_playlists(self.id)
