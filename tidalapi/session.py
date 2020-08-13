# -*- coding: utf-8 -*-

# Copyright (C) 2019-2020 morguldir
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

import base64
import logging
import random
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

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

log = logging.getLogger('__NAME__')

SearchTypes = [tidalapi.artist.Artist,
               tidalapi.album.Album,
               tidalapi.media.Track,
               tidalapi.media.Video,
               tidalapi.playlist.Playlist]


class Quality(Enum):
    lossless = 'LOSSLESS'
    high = 'HIGH'
    low = 'LOW'
    # Not implemented
    master = 'HI_RES'


class VideoQuality(Enum):
    high = 'HIGH'
    medium = 'MEDIUM'
    low = 'LOW'


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
        if not self.alac:
            self.api_token = list((base64.b64decode("d3RjaThkamFfbHlhQnBKaWQuMkMwb3puT2ZtaXhnMA==").decode()))
        else:
            tok = "".join(([chr(ord(x)+3) for x in token[-6:]]))
            token = token[:9]
            token += tok
            self.api_token = list((base64.b64decode("X3REaVNkVGFvbG5hMXBraUMuOEZwckFxQmlubFRqdw==").decode()))
        for word in token:
            self.api_token.remove(word)
        self.api_token = "".join(self.api_token)


class Session(object):
    """
    Object for interacting with the TIDAL api and
    """

    def __init__(self, config=Config()):
        self.session_id = None
        self.country_code = None
        self.user = None
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

        self.parse_user = tidalapi.User(self, None).parse

        # Dictionary to convert between models from this library, to the text they, and to the parsing function.
        # It also helps in converting the other way around. All the information about artist is stored at the
        # Same index, which means you can get the index of the model, and then get the text using that index.
        # There probably is a better way to do this, but this was sadly the most readable way i found of doing it.
        self.type_conversions = {
            'identifier': ['artists', 'albums', 'tracks', 'videos', 'playlists'],
            'type': SearchTypes,
            'parse': [self.parse_artist, self.parse_album, self.parse_track, self.parse_video, self.parse_playlist]
        }

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

    def _invert_alac(self):
        quality = Quality(self.config.quality)
        video_quality = Quality(self.config.video_quality)
        alac = not self.config.alac
        self.config = Config(quality=quality, video_quality=video_quality, alac=alac)

    def login(self, username, password):
        """
        Logs in to the TIDAL api.

        :param username: The TIDAL username
        :param password: The password to your TIDAL account
        :return: Returns true if we think the login was successful.
        """
        log.warning("Test")

        url = urljoin(self.config.api_location, 'login/username')
        headers = {"X-Tidal-Token": self.config.api_token}
        payload = {
            'username': username,
            'password': password,
            'clientUniqueKey': format(random.getrandbits(64), '02x')
        }
        request = self.request_session.post(url, data=payload, headers=headers)

        # If one of the tokens get revoked we will try to switch to the other one
        if request.reason == "Unauthorized":
            self._invert_alac()
            log.debug("Changing ALAC option to %s because of expired token", self.config.alac)
            headers["X-Tidal-Token"] = self.config.api_token
            request = self.request_session.post(url, data=payload, headers=headers)

        if not request.ok:
            log.error("Login failed: %s", request.text)
            request.raise_for_status()

        body = request.json()
        self.session_id = body['sessionId']
        self.country_code = body['countryCode']
        self.user = tidalapi.User(self, user_id=body['userId']).factory()
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
            index = self.type_conversions['type'].index(model)
            types.append(self.type_conversions['identifier'][index])

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
            index = self.type_conversions['identifier'].index(json_obj['topHit']['type'].lower())
            parse_top_hit = self.type_conversions['parse'][index]
            result['top_hit'] = self.request.map_json(json_obj['topHit']['value'], parse_top_hit)
        else:
            result['top_hit'] = None

        return result

    def check_login(self):
        """ Returns true if current session is valid, false otherwise. """
        if self.user is None or not self.user.id or not self.session_id:
            return False
        url = urljoin(self.config.api_location, 'users/%s/subscription' % self.user.id)
        return requests.get(url, params={'sessionId': self.session_id}).ok

    def playlist(self, playlist_id=None):
        """
        Function to create a playlist object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.Playlist(session=session, playlist_id=playlist_id) <.Playlist>` internally

        :param playlist_id: (Optional) The TIDAL id of the playlist. You may want access to the methods without an id.
        :return: Returns a :class:`.Playlist` object that has access to the session instance used.
        """

        return tidalapi.Playlist(session=self, playlist_id=playlist_id).factory()

    def track(self, track_id=None):
        """
        Function to create a Track object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.Track(session=session, track_id=track_id) <.Track>` internally

        :param track_id: (Optional) The TIDAL id of the Track. You may want access to the methods without an id.
        :return: Returns a :class:`.Track` object that has access to the session instance used.
        """

        return tidalapi.Track(session=self, media_id=track_id)

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

    def get_user(self, user_id=None):
        """
        Function to create a User object with access to the session instance in a smoother way.
        Calls :class:`tidalapi.User(session=session, user_id=user_id) <.User>` internally

        :param user_id: (Optional) The TIDAL id of the User. You may want access to the methods without an id.
        :return: Returns a :class:`.User` object that has access to the session instance used.
        """

        return tidalapi.User(session=self, user_id=user_id).factory()
