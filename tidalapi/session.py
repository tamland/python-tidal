# -*- coding: utf-8 -*-

# Copyright (C) 2019-2022 morguldir
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

import concurrent.futures
import datetime
import base64
import logging
import random
import time
import uuid
from enum import Enum

import requests

import tidalapi.playlist
import tidalapi.request
import tidalapi.user
import tidalapi.media
import tidalapi.artist
import tidalapi.album
import tidalapi.genre
import tidalapi.mix

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

log = logging.getLogger('__NAME__')

SearchTypes = [tidalapi.artist.Artist,
               tidalapi.album.Album,
               tidalapi.media.Track,
               tidalapi.media.Video,
               tidalapi.playlist.Playlist,
               None]


class Quality(Enum):
    lossless = 'LOSSLESS'
    high = 'HIGH'
    low = 'LOW'
    master = 'HI_RES'


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
    """
    Configuration for TIDAL services.

    The maximum item_limit is 10000, and some endpoints have a maximum of 100 items, which will be shown in the docs.
    In cases where the maximum is 100 items, you will have to use offsets to get more than 100 items.
    Note that changing the ALAC option requires you to log in again, and for you to create a new config object
    IMPORTANT: ALAC=false will mean that video streams turn into audio-only streams.
               Additionally, num_videos will turn into num_tracks in playlists.
    """
    def __init__(self, quality=Quality.high, video_quality=VideoQuality.high, item_limit=1000, alac=True):
        self.quality = quality.value
        self.video_quality = video_quality.value
        self.api_location = 'https://api.tidal.com/v1/'
        self.image_url = "https://resources.tidal.com/images/%s/%ix%i.jpg"
        self.video_url = "https://resources.tidal.com/videos/%s/%ix%i.mp4"

        self.alac = alac

        if item_limit > 10000:
            log.warning("Item limit was set above 10000, which is not supported by TIDAL, setting to 10000")
            self.item_limit = 10000
        else:
            self.item_limit = item_limit

        self.api_token = \
            eval(u'\x67\x6c\x6f\x62\x61\x6c\x73'.
                 encode("437"))()[u"\x5f\x5f\x6e\x61\x6d\x65\x5f\x5f".
                                  encode("".join(map(chr, [105, 105, 99, 115, 97][::-1]))).
                                  decode("".join(map(chr, [117, 116, 70, 95, 56])))]
        self.api_token += '.' + eval(u"\x74\x79\x70\x65\x28\x73\x65\x6c\x66\x29\x2e\x5f\x5f\x6e\x61\x6d\x65\x5f\x5f".
                                     encode("".join(map(chr, [105, 105, 99, 115, 97][::-1]))).
                                     decode("".join(map(chr, [117, 116, 70, 95, 56]))))
        token = self.api_token
        token = token[:8] + token[16:]
        self.api_token = list((base64.b64decode("d3RjaThkamFfbHlhQnBKaWQuMkMwb3puT2ZtaXhnMA==").decode()))
        tok = "".join(([chr(ord(x)-2) for x in token[-6:]]))
        token2 = token
        token = token[:9]
        token += tok
        tok2 = "".join(([chr(ord(x)-2) for x in token[:-7]]))
        token = token[8:]
        token = tok2 + token
        self.api_token = list((base64.b64decode("enJVZzRiWF9IalZfVm5rZ2MuMkF0bURsUGRvZzRldA==").decode()))
        for word in token:
            self.api_token.remove(word)
        self.api_token = "".join(self.api_token)
        string = ""
        save = False
        if not isinstance(token2, str):
            save = True
            string = "".encode('ISO-8859-1')
            token2 = token2.encode('ISO-8859-1')
        tok = string.join(([chr(ord(x) + 24) for x in token2[:-7]]))
        token2 = token2[8:]
        token2 = tok + token2
        tok2 = string.join(([chr(ord(x)+23) for x in token2[-6:]]))
        token2 = token2[:9]
        token2 += tok2
        self.client_id = list((base64.b64decode("VoxKgUt8aHlEhEZ5cYhKgVAucVp2hnOFUH1WgE5+QlY2"
                                                "dWtYVEptd2x2YnR0UDd3bE1scmM3MnNlND0=").decode('ISO-8859-1')))
        if save:
            token2.decode('ISO-8859-1').encode('utf-16')
            self.client_id = [x.encode('ISO-8859-1') for x in self.client_id]
        for word in token2:
            self.client_id.remove(word)
        self.client_id = "".join(self.client_id)
        self.client_secret = self.client_id
        self.client_id = self.api_token


class Case(Enum):
    pascal = id
    scream = id
    lower = id


class Session(object):
    """
    Object for interacting with the TIDAL api and
    """

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
        self.config = config
        self.request_session = requests.Session()

        # Objects for keeping the session across all modules.
        self.request = tidalapi.Requests(session=self)
        self.genre = tidalapi.Genre(session=self)

        self.parse_album = self.album().parse
        self.parse_artist = self.artist().parse_artist
        self.parse_artists = self.artist().parse_artists
        self.parse_playlist = self.playlist().parse

        self.parse_track = self.track().parse_track
        self.parse_video = self.video().parse_video
        self.parse_media = self.track().parse_media
        self.parse_mix = self.mix().parse

        self.parse_user = tidalapi.User(self, None).parse
        self.page = tidalapi.Page(self, None)
        self.parse_page = self.page.parse

        # Dictionary to convert between models from this library, to the text they, and to the parsing function.
        # It also helps in converting the other way around. All the information about artist is stored at the
        # Same index, which means you can get the index of the model, and then get the text using that index.
        # There probably is a better way to do this, but this was sadly the most readable way i found of doing it.
        self.type_conversions = {
            'identifier': ['artists', 'albums', 'tracks', 'videos', 'playlists', 'mixs'],
            'type': SearchTypes,
            'parse': [self.parse_artist, self.parse_album, self.parse_track,
                      self.parse_video, self.parse_playlist, self.parse_mix]
        }

    def convert_type(self, search, search_type='identifier', output='identifier', case=Case.lower, suffix=True):
        index = self.type_conversions[search_type].index(search)
        result = self.type_conversions[output][index]

        if output == 'identifier':
            if suffix is False:
                result = result.strip('s')
            if case == Case.scream:
                result = result.lower()
            elif case == Case.pascal:
                result = result[0].upper() + result[1:]

        return result

    def load_session(self, session_id, country_code=None, user_id=None):
        """
        Establishes TIDAL login details using a previous session id.
        May return true if the session-id is invalid/expired, you should verify the login afterwards.

        :param session_id: The UUID of the session you want to use.
        :param country_code: (Optional) Two-letter country code.
        :param user_id: (Optional) The number identifier of the user.
        :return: False if we know the session_id is incorrect, otherwise True
        """
        try:
            uuid.UUID(session_id)
        except ValueError:
            log.error("Session id did not have a valid UUID format")
            return False

        self.session_id = session_id
        if not user_id or not country_code:
            request = self.request.request('GET', 'sessions').json()
            country_code = request['countryCode']
            user_id = request['userId']

        self.country_code = country_code
        self.user = tidalapi.User(self, user_id=user_id).factory()
        return True

    def load_oauth_session(self, token_type, access_token, refresh_token=None, expiry_time=None):
        """
        Login to TIDAL using details from a previous OAuth login, automatically
        refreshes expired access tokens if refresh_token is supplied as well.

        :param token_type: The type of token, e.g. Bearer
        :param access_token: The access token received from an oauth login or refresh
        :param refresh_token: (Optional) A refresh token that lets you get a new access token after it has expired
        :param expiry_time: (Optional) The datetime the access token will expire
        :return: True if we believe the log in was successful, otherwise false.
        """
        self.token_type = token_type
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiry_time = expiry_time

        request = self.request.request('GET', 'sessions')
        json = request.json()
        if not request.ok:
            return False

        self.session_id = json['sessionId']
        self.country_code = json['countryCode']
        self.user = tidalapi.User(self, user_id=json['userId']).factory()

        return True

    def login(self, username, password):
        """
        Logs in to the TIDAL api.

        :param username: The TIDAL username
        :param password: The password to your TIDAL account
        :return: Returns true if we think the login was successful.
        """
        url = urljoin(self.config.api_location, 'login/username')
        headers = {"X-Tidal-Token": self.config.api_token}
        payload = {
            'username': username,
            'password': password,
            'clientUniqueKey': format(random.getrandbits(64), '02x')
        }
        request = self.request_session.post(url, data=payload, headers=headers)

        if not request.ok:
            log.error("Login failed: %s", request.text)
            request.raise_for_status()

        body = request.json()
        self.session_id = body['sessionId']
        self.country_code = body['countryCode']
        self.user = tidalapi.User(self, user_id=body['userId']).factory()
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
            'client_id': self.config.client_id,
            'scope': 'r_usr w_usr w_sub'
        }

        request = self.request_session.post(url, params)

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
        session = self.request.request('GET', 'sessions')
        json = session.json()
        self.session_id = json['sessionId']
        self.country_code = json['countryCode']
        self.user = tidalapi.User(self, user_id=json['userId']).factory()

    def _wait_for_link_login(self, json):
        expiry = json['expiresIn']
        interval = json['interval']
        device_code = json['deviceCode']
        url = 'https://auth.tidal.com/v1/oauth2/token'
        params = {
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'device_code': device_code,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'scope': 'r_usr w_usr w_sub'
        }
        while expiry > 0:
            request = self.request_session.post(url, params)
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
        Retrieves a new access token using the specified parameters, updating the current access token

        :param refresh_token: The refresh token retrieved when using the OAuth login.
        :return: True if we believe the token was successfully refreshed, otherwise False
        """
        url = 'https://auth.tidal.com/v1/oauth2/token'
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret
        }

        request = self.request_session.post(url, params)
        json = request.json()
        if not request.ok:
            log.warning("The refresh token has expired, a new login is required.")
            return False
        self.access_token = json['access_token']
        self.expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=json['expires_in'])
        self.token_type = json['token_type']
        return True

    def search(self, query, models=None, limit=50, offset=0):
        """
        Searches TIDAL with the specified query, you can also specify what models you want to search for.
        While you can set the offset, there aren't more than 300 items available in a search.

        :param query: The string you want to search for
        :param models: A list of tidalapi models you want to include in the search.
            Valid models are :class:`.Artist`, :class:`.Album`, :class:`.Track`, :class:`.Video`, :class:`.Playlist`
        :param limit: The amount of items you want included, up to 300.
        :param offset: The index you want to start searching at.
        :return: Returns a dictionary of the different models, with the dictionary values containing the search results.
            The dictionary also contains a 'top_hit' result for the most relevant result, limited to the specified types
        """
        if not models:
            models = SearchTypes

        types = []
        # This converts the specified TIDAL models in the models list into the text versions so we can parse it.
        for model in models:
            if model not in SearchTypes:
                raise ValueError("Tried to search for an invalid type")
            types.append(self.convert_type(model, 'type'))

        params = {
            'query': query,
            'limit': limit,
            'offset': offset,
            'types': ",".join(types)
        }

        json_obj = self.request.request('GET', 'search', params=params).json()

        result = {
            'artists': self.request.map_json(json_obj['artists'], self.parse_artist),
            'albums': self.request.map_json(json_obj['albums'], self.parse_album),
            'tracks': self.request.map_json(json_obj['tracks'], self.parse_track),
            'videos': self.request.map_json(json_obj['videos'], self.parse_video),
            'playlists': self.request.map_json(json_obj['playlists'], self.parse_playlist)
        }

        # Find the type of the top hit so we can parse it
        if json_obj['topHit']:
            top_type = json_obj['topHit']['type'].lower()
            parse = self.convert_type(top_type, output='parse')
            result['top_hit'] = self.request.map_json(json_obj['topHit']['value'], parse)
        else:
            result['top_hit'] = None

        return result

    def check_login(self):
        """ Returns true if current session is valid, false otherwise. """
        if self.user is None or not self.user.id or not self.session_id:
            return False
        return self.request.basic_request('GET', 'users/%s/subscription' % self.user.id).ok

    def playlist(self, playlist_id=None):
        """
        Function to create a playlist object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.Playlist(session=session, playlist_id=playlist_id) <.Playlist>` internally

        :param playlist_id: (Optional) The TIDAL id of the playlist. You may want access to the methods without an id.
        :return: Returns a :class:`.Playlist` object that has access to the session instance used.
        """

        return tidalapi.Playlist(session=self, playlist_id=playlist_id).factory()

    def track(self, track_id=None, with_album=False):
        """
        Function to create a Track object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.Track(session=session, track_id=track_id) <.Track>` internally

        :param track_id: (Optional) The TIDAL id of the Track. You may want access to the methods without an id.
        :param with_album: (Optional) Whether to fetch the complete :class:`.Album` for the track or not
        :return: Returns a :class:`.Track` object that has access to the session instance used.
        """

        item = tidalapi.Track(session=self, media_id=track_id)
        if item.album and with_album:
            album = self.album(item.album.id)
            if album:
                item.album = album

        return item

    def video(self, video_id=None):
        """
        Function to create a Video object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.Video(session=session, video_id=video_id) <.Video>` internally

        :param video_id: (Optional) The TIDAL id of the Video. You may want access to the methods without an id.
        :return: Returns a :class:`.Video` object that has access to the session instance used.
        """

        return tidalapi.Video(session=self, media_id=video_id)

    def artist(self, artist_id=None):
        """
        Function to create a Artist object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.Artist(session=session, artist_id=artist_id) <.Artist>` internally

        :param artist_id: (Optional) The TIDAL id of the Artist. You may want access to the methods without an id.
        :return: Returns a :class:`.Artist` object that has access to the session instance used.
        """

        return tidalapi.Artist(session=self, artist_id=artist_id)

    def album(self, album_id=None):
        """
        Function to create a Album object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.Album(session=session, album_id=album_id) <.Album>` internally

        :param album_id: (Optional) The TIDAL id of the Album. You may want access to the methods without an id.
        :return: Returns a :class:`.Album` object that has access to the session instance used.
        """

        return tidalapi.Album(session=self, album_id=album_id)

    def mix(self, mix_id=None):
        """
        Function to create a mix object with access to the session instance smoothly
        Calls :class:`tidalapi.Mix(session=session, mix_id=mix_id) <.Album>` internally

        :param mix_id: (Optional) The TIDAL id of the Mix. You may want access to the mix methods without an id.
        :return: Returns a :class:`.Mix` object that has access to the session instance used.
        """

        return tidalapi.Mix(session=self, mix_id=mix_id)

    def get_user(self, user_id=None):
        """
        Function to create a User object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.User(session=session, user_id=user_id) <.User>` internally

        :param user_id: (Optional) The TIDAL id of the User. You may want access to the methods without an id.
        :return: Returns a :class:`.User` object that has access to the session instance used.
        """

        return tidalapi.User(session=self, user_id=user_id).factory()

    def home(self):
        """
        Retrieves the Home page, as seen on https://listen.tidal.com

        :return: A :class:`.Page` object with the :class:`.PageCategory` list from the home page
        """
        return self.page.get("pages/home")

    def explore(self):
        """
        Retrieves the Explore page, as seen on https://listen.tidal.com/view/pages/explore

        :return: A :class:`.Page` object with the :class:`.PageCategory` list from the explore page
        """
        return self.page.get("pages/explore")

    def videos(self):
        """
        Retrieves the :class:`Videos<.Video>` page, as seen on https://listen.tidal.com/view/pages/videos

        :return: A :class:`.Page` object with a :class:`<.PageCategory>` list from the videos page
        """
        return self.page.get("pages/videos")

    def genres(self):
        """
        Retrieves the global Genre page, as seen on https://listen.tidal.com/view/pages/genre_page

        :return: A :class:`.Page` object with the :class:`.PageCategory` list from the genre page
        """
        return self.page.get("pages/genre_page")

    def local_genres(self):
        """
        Retrieves the local Genre page, as seen on https://listen.tidal.com/view/pages/genre_page_local

        :return: A :class:`.Page` object with the :class:`.PageLinks` list from the local genre page
        """
        return self.page.get("pages/genre_page_local")

    def moods(self):
        """
        Retrieves the mood page, as seen on https://listen.tidal.com/view/pages/moods

        :return: A :class:`.Page` object with the :class:`.PageLinks` list from the moods page
        """
        return self.page.get("pages/moods")

    def mixes(self):
        """
        Retrieves the current users mixes, as seen on https://listen.tidal.com/view/pages/my_collection_my_mixes

        :return: A list of :class:`.Mix`
        """
        return self.page.get("pages/my_collection_my_mixes")
