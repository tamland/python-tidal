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

import re
import datetime
import random
import json
import logging
import requests
from requests.packages import urllib3
from collections import Iterable
from .models import UserInfo, Subscription, SubscriptionType, Quality
from .models import Artist, Album, Track, Video, Playlist, BrowsableMedia, PlayableMedia, Promotion, SearchResult, Category
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


log = logging.getLogger(__name__)


class Config(object):
    def __init__(self, quality=Quality.high):
        self.quality = quality
        self.api_location = 'https://api.tidal.com/v1/'
        self.api_token = 'kgsOOmYk3zShYrNP'     # Android Token that works for everything
        self.preview_token = "8C7kRFdkaRp0dLBp" # Token for Preview Mode


class Session(object):

    def __init__(self, config=Config()):
        """:type _config: :class:`Config`"""
        self._config = config
        self.session_id = None
        self.user = None
        self.country_code = 'US'   # Enable Trial Mode
        self.client_unique_key = None
        urllib3.disable_warnings() # Disable OpenSSL Warnings in URLLIB3

    def logout(self):
        self.session_id = None
        self.user = None

    def load_session(self, session_id, country_code, user_id=None, subscription_type=None, unique_key=None):
        self.session_id = session_id
        self.client_unique_key = unique_key
        self.country_code = country_code
        if not self.country_code:
            # Set Local Country Code to enable Trial Mode 
            self.country_code = self.local_country_code()
        if user_id:
            self.user = self.init_user(user_id=user_id, subscription_type=subscription_type)
        else:
            self.user = None

    def generate_client_unique_key(self):
        return format(random.getrandbits(64), '02x')

    def login(self, username, password, subscription_type=None):
        self.logout()
        if not username or not password:
            return False
        if not subscription_type:
            # Set Subscription Type corresponding to the given playback quality
            subscription_type = SubscriptionType.hifi if self._config.quality == Quality.lossless else SubscriptionType.premium
        if not self.client_unique_key:
            # Generate a random client key if no key is given
            self.client_unique_key = self.generate_client_unique_key()
        url = urljoin(self._config.api_location, 'login/username')
        headers = { "X-Tidal-Token": self._config.api_token }
        payload = {
            'username': username,
            'password': password,
            'clientUniqueKey': self.client_unique_key
        }
        log.debug('Using Token "%s" with clientUniqueKey "%s"' % (self._config.api_token, self.client_unique_key))
        r = requests.post(url, data=payload, headers=headers)
        if not r.ok:
            try:
                msg = r.json().get('userMessage')
            except:
                msg = r.reason
            log.error(msg)
        else:
            try:
                body = r.json()
                self.session_id = body['sessionId']
                self.country_code = body['countryCode']
                self.user = self.init_user(user_id=body['userId'], subscription_type=subscription_type)
            except:
                log.error('Login failed.')
                self.logout()

        return self.is_logged_in

    def init_user(self, user_id, subscription_type):
        return User(self, user_id=user_id, subscription_type=subscription_type)

    def local_country_code(self):
        url = urljoin(self._config.api_location, 'country/context')
        headers = { "X-Tidal-Token": self._config.api_token}
        r = requests.request('GET', url, params={'countryCode': 'WW'}, headers=headers)
        if not r.ok:
            return 'US'
        return r.json().get('countryCode')

    @property
    def is_logged_in(self):
        return True if self.session_id and self.country_code and self.user else False

    def check_login(self):
        """ Returns true if current session is valid, false otherwise. """
        if not self.is_logged_in:
            return False
        self.user.subscription = self.get_user_subscription(self.user.id)
        return True if self.user.subscription != None else False

    def request(self, method, path, params=None, data=None, headers=None):
        request_headers = {}
        request_params = {
            'countryCode': self.country_code
        }
        if headers:
            request_headers.update(headers)
        if params:
            request_params.update(params)
        if request_params.get('offset', 1) == 0:
            request_params.pop('offset', 1) # Remove Zero Offset from Params
        url = urljoin(self._config.api_location, path)
        if self.is_logged_in:
            # Request with API Session if SessionId is not given in headers parameter
            if not 'X-Tidal-SessionId' in request_headers:
                request_headers.update({'X-Tidal-SessionId': self.session_id})
        else:
            # Request with Preview-Token. Remove SessionId if given via headers parameter
            request_headers.pop('X-Tidal-SessionId', None)
            request_params.update({'token': self._config.preview_token})
        r = requests.request(method, url, params=request_params, data=data, headers=request_headers)
        log.debug("%s %s" % (method, r.request.url))
        if not r.ok:
            log.error(r.url)
            try:
                log.error(r.json().get('userMessage'))
            except:
                log.error(r.reason)
        r.raise_for_status()
        if r.content and log.isEnabledFor(logging.INFO):
            log.info("response: %s" % json.dumps(r.json(), indent=4))
        return r

    def get_user(self, user_id):
        return self._map_request('users/%s' % user_id, ret='user')

    def get_user_subscription(self, user_id):
        return self._map_request('users/%s/subscription' % user_id, ret='subscription')

    def get_user_playlists(self, user_id):
        return self._map_request('users/%s/playlists' % user_id, ret='playlists')

    def get_playlist(self, playlist_id):
        return self._map_request('playlists/%s' % playlist_id, ret='playlist')

    def get_playlist_tracks(self, playlist_id, offset=0, limit=9999):
        items = self._map_request('playlists/%s/tracks' % playlist_id, params={'offset': offset, 'limit': limit}, ret='tracks')
        track_no = offset
        for item in items:
            item._playlist_id = playlist_id
            item._playlist_pos = track_no
            track_no += 1
        return items

    def get_playlist_items(self, playlist_id=None, playlist=None, offset=0, limit=9999, ret='playlistitems'):
        if not playlist:
            playlist = self.get_playlist(playlist_id)
        # Don't read empty playlists
        if not playlist or playlist.numberOfItems == 0:
            return []
        itemCount = playlist.numberOfItems - offset
        remaining = min(itemCount,limit)
        result = []
        # Number of Items is limited to 100, so read multiple times if more than 100 entries are requested
        while remaining > 0:
            nextLimit = min(100,remaining)
            items = self._map_request('playlists/%s/items' % playlist.id, params={'offset': offset, 'limit': nextLimit}, ret='playlistitems')
            if items:
                track_no = offset
                for item in items:
                    item._playlist_id = playlist.id
                    item._playlist_pos = track_no
                    item._etag = playlist._etag
                    item._playlist_name = playlist.title
                    item._playlist_type = playlist.type
                    track_no += 1
                remaining -= len(items)
                result += items
            offset += 100
        if ret.startswith('track'):
            # Return tracks only
            result = [item for item in result if isinstance(item, Track)]
        elif ret.startswith('video'):
            # Return videos only
            result = [item for item in result if isinstance(item, Video)]
        return result

    def get_album(self, album_id):
        return self._map_request('albums/%s' % album_id, ret='album')

    def get_album_tracks(self, album_id):
        return self._map_request('albums/%s/tracks' % album_id, ret='tracks')

    def get_album_items(self, album_id, ret='playlistitems'):
        offset = 0
        remaining = 9999
        result = []
        # Number of Items is limited to 100, so read multiple times if more than 100 entries are requested
        while remaining > 0:
            items = self._map_request('albums/%s/items' % album_id, params={'offset': offset, 'limit': 100}, ret='playlistitems')
            if items:
                if remaining == 9999:
                    remaining = items[0]._totalNumberOfItems
                remaining -= len(items)
                result += items
            offset += 100
        if ret.startswith('track'):
            # Return tracks only
            result = [item for item in result if isinstance(item, Track)]
        elif ret.startswith('video'):
            # Return videos only
            result = [item for item in result if isinstance(item, Video)]
        return result

    def get_artist(self, artist_id):
        return self._map_request('artists/%s' % artist_id, ret='artist')

    def get_artist_albums(self, artist_id, offset=0, limit=999):
        return self._map_request('artists/%s/albums' % artist_id, params={'offset': offset, 'limit': limit}, ret='albums')

    def get_artist_albums_ep_singles(self, artist_id, offset=0, limit=999):
        return self._map_request('artists/%s/albums' % artist_id, params={'filter': 'EPSANDSINGLES', 'offset': offset, 'limit': limit}, ret='albums')

    def get_artist_albums_other(self, artist_id, offset=0, limit=999):
        return self._map_request('artists/%s/albums' % artist_id, params={'filter': 'COMPILATIONS', 'offset': offset, 'limit': limit}, ret='albums')

    def get_artist_top_tracks(self, artist_id, offset=0, limit=999):
        return self._map_request('artists/%s/toptracks' % artist_id, params={'offset': offset, 'limit': limit}, ret='tracks')

    def get_artist_videos(self, artist_id, offset=0, limit=999):
        return self._map_request('artists/%s/videos' % artist_id, params={'offset': offset, 'limit': limit}, ret='videos')

    def _cleanup_text(self, text):
        clean_text = re.sub(r"\[.*\]", ' ', text)         # Remove Tags: [wimpLink ...] [/wimpLink]
        clean_text = re.sub(r"<br.>", '\n', clean_text)   # Replace Tags: <br/> with NewLine
        return clean_text

    def get_artist_bio(self, artist_id):
        bio = self.request('GET', 'artists/%s/bio' % artist_id, params={'includeImageLinks': 'false'}).json()
        return self._cleanup_text(bio.get('text', ''))

    def get_artist_info(self, artist_id):
        bio = self.request('GET', 'artists/%s/bio' % artist_id, params={'includeImageLinks': 'false'}).json()
        if bio.get('summary', None):
            bio.update({'summary': self._cleanup_text(bio.get('summary', ''))})
        if bio.get('text', None):
            bio.update({'text': self._cleanup_text(bio.get('text', ''))})
        return bio

    def get_artist_similar(self, artist_id, offset=0, limit=999):
        return self._map_request('artists/%s/similar' % artist_id, params={'offset': offset, 'limit': limit}, ret='artists')

    def get_artist_radio(self, artist_id, offset=0, limit=999):
        return self._map_request('artists/%s/radio' % artist_id, params={'offset': offset, 'limit': limit}, ret='tracks')

    def get_artist_playlists(self, artist_id):
        return self._map_request('artists/%s/playlistscreatedby' % artist_id, ret='playlists')

    def get_featured(self, group=None, types=['PLAYLIST'], limit=999):
        params = {'limit': limit,
                  'clientType': 'BROWSER',
                  'subscriptionType': SubscriptionType.hifi if not self.is_logged_in else self.user.subscription.type}
        if group:
            params.update({'group': group})      # RISING | DISCOVERY | NEWS
        items = self.request('GET', 'promotions', params=params).json()['items']
        return [self._parse_promotion(item) for item in items if item['type'] in types]

    def get_category_items(self, group):
        items = map(self._parse_category, self.request('GET', group).json())
        for item in items:
            item._group = group
        return items

    def get_category_content(self, group, path, content_type, offset=0, limit=999):
        return self._map_request('/'.join([group, path, content_type]), params={'offset': offset, 'limit': limit}, ret=content_type)

    def get_featured_items(self, content_type, group, path='featured', offset=0, limit=999):
        return self.get_category_content(path, group, content_type, offset, limit)

    def get_moods(self):
        return self.get_category_items('moods')

    def get_mood_playlists(self, mood_id):
        return self.get_category_content('moods', mood_id, 'playlists')

    def get_genres(self):
        return self.get_category_items('genres')

    def get_genre_items(self, genre_id, content_type):
        return self.get_category_content('genres', genre_id, content_type)

    def get_movies(self):
        items = self.get_category_items('movies')
        movies = []
        for item in items:
            movies += self.get_category_content('movies', item.path, 'videos')
        return movies

    def get_shows(self):
        items = self.get_category_items('shows')
        shows = []
        for item in items:
            shows += self.get_category_content('shows', item.path, 'playlists')
        return shows

    def get_track_radio(self, track_id, offset=0, limit=999):
        return self._map_request('tracks/%s/radio' % track_id, params={'offset': offset, 'limit': limit}, ret='tracks')

    def get_track(self, track_id, withAlbum=False):
        item = self._map_request('tracks/%s' % track_id, ret='track')
        if item.album and withAlbum:
            album = self.get_album(item.album.id)
            if album:
                item.album = album
        return item

    def get_video(self, video_id):
        return self._map_request('videos/%s' % video_id, ret='video')

    def get_recommended_items(self, content_type, item_id, offset=0, limit=999):
        return self._map_request('%s/%s/recommendations' % (content_type, item_id), params={'offset': offset, 'limit': limit}, ret=content_type)

    def _map_request(self, url, method='GET', params=None, data=None, headers=None, ret=None):
        r = self.request(method, url, params=params, data=data, headers=headers)
        if not r.ok:
            return [] if ret.endswith('s') else None
        json_obj = r.json()
        if 'items' in json_obj:
            items = json_obj.get('items')
            result = []
            offset = 0
            if params and 'offset' in params:
                offset = params.get('offset')
            itemPosition = offset
            try:
                numberOfItems = int('0%s' % json_obj.get('totalNumberOfItems')) if 'totalNumberOfItems' in json_obj else 9999
            except:
                numberOfItems = 9999
            log.debug('NumberOfItems=%s, %s items in list' % (numberOfItems, len(items)))
            for item in items:
                retType = ret
                if 'type' in item and ret.startswith('playlistitem'):
                    retType = item['type']
                if 'item' in item:
                    item = item['item']
                elif 'track' in item and ret.startswith('track'):
                    item = item['track']
                elif 'video' in item and ret.startswith('video'):
                    item = item['video']
                nextItem = self._parse_one_item(item, retType)
                if isinstance(nextItem, BrowsableMedia):
                    nextItem._itemPosition = itemPosition
                    nextItem._offset = offset
                    nextItem._totalNumberOfItems = numberOfItems
                result.append(nextItem)
                itemPosition = itemPosition + 1
        else:
            result = self._parse_one_item(json_obj, ret)
            if isinstance(result, Playlist) and result.type == 'USER':
                # Get ETag of Playlist which must be used to add/remove entries of playlists
                try: 
                    result._etag = r.headers._store['etag'][1]
                except:
                    result._etag = None
                    log.error('No ETag in response header for playlist "%s" (%s)' % (json_obj.get('title'), json_obj.get('id')))
        return result

    def get_media_url(self, track_id, quality=None):
        if self.is_logged_in:
            params = {'soundQuality': quality if quality else self._config.quality}
            # Request with second SessionId because FLAC Streaming needs a different Login Token
            r = self.request('GET', 'tracks/%s/streamUrl' % track_id, params)
            if r.ok:
                json_obj = r.json()
                url = json_obj.get('url', None)
                if params.get('soundQuality') == Quality.lossless and json_obj.get('encryptionKey', False) and not '.flac' in url:
                    # Got Encrypted Stream. Retry with HIGH Quality
                    log.warning(url)
                    log.warning('Got encryptionKey "%s" for track %s, trying HIGH Quality ...' % (json_obj.get('encryptionKey', ''), track_id))
                    return self.get_media_url(track_id, quality=Quality.high)
        else:
            r = self.request('GET', 'tracks/%s/previewurl' % track_id)
            url = r.json().get('url', None)
        if not r.ok:
            r.raise_for_status()
        return url

    def get_video_url(self, video_id):
        if self.is_logged_in:
            r = self.request('GET', 'videos/%s/streamUrl' % video_id)
        else:
            r = self.request('GET', 'videos/%s/previewurl' % video_id)
        if not r.ok:
            r.raise_for_status()
        return r.json().get('url', None)

    def search(self, field, value, limit=50):
        params = {
            'query': value,
            'limit': limit,
        }
        if isinstance(field, basestring):
            what = field.upper()
            params.update({'types': what if what == 'ALL' or what.endswith('S') else what + 'S'})
        elif isinstance(field, Iterable):
            params.update({'types': ','.join(field)})
        return self._map_request('search', params=params, ret='search')

#------------------------------------------------------------------------------
# Parse JSON Data into Media-Item-Objects
#------------------------------------------------------------------------------

    def _parse_one_item(self, json_obj, ret=None):
        parse = None
        if ret.startswith('user'):
            parse = self._parse_user
        elif ret.startswith('subscription'):
            parse = self._parse_subscription
        elif ret.startswith('artist'):
            parse = self._parse_artist
        elif ret.startswith('album'):
            parse = self._parse_album
        elif ret.startswith('track'):
            parse = self._parse_track
        elif ret.startswith('video'):
            parse = self._parse_video
        elif ret.startswith('playlist'):
            parse = self._parse_playlist
        elif ret.startswith('category'):
            parse = self._parse_category
        elif ret.startswith('search'):
            parse = self._parse_search
        else:
            raise NotImplementedError()
        oneItem = parse(json_obj)
        return oneItem

    def _parse_user(self, json_obj):
        return UserInfo(**json_obj)

    def _parse_subscription(self, json_obj):
        return Subscription(**json_obj)

    def _parse_artist(self, json_obj):
        artist = Artist(**json_obj)
        if self.is_logged_in and self.user.favorites:
            artist._isFavorite = self.user.favorites.isFavoriteArtist(artist.id)
        return artist

    def _parse_all_artists(self, artist_id, json_obj):
        allArtists = []
        ftArtists = []
        for item in json_obj:
            nextArtist = self._parse_artist(item)
            allArtists.append(nextArtist)
            if nextArtist.id <> artist_id:
                ftArtists.append(nextArtist)
        return (allArtists, ftArtists)

    def _parse_album(self, json_obj, artist=None):
        album = Album(**json_obj)
        if artist:
            album.artist = artist
        elif 'artist' in json_obj:
            album.artist = self._parse_artist(json_obj['artist'])
        elif 'artists' in json_obj:
            album.artist = self._parse_artist(json_obj['artists'][0])
        if 'artists' in json_obj:
            album.artists, album._ftArtists = self._parse_all_artists(album.artist.id, json_obj['artists'])
        else:
            album.artists = [album.artist]
            album._ftArtists = []
        if self.is_logged_in and self.user.favorites:
            album._isFavorite = self.user.favorites.isFavoriteAlbum(album.id)
        return album

    def _parse_playlist(self, json_obj):
        playlist = Playlist(**json_obj)
        if self.is_logged_in and self.user.favorites:
            playlist._isFavorite = self.user.favorites.isFavoritePlaylist(playlist.id)
        return playlist

    def _parse_promotion(self, json_obj):
        item = Promotion(**json_obj)
        if self.is_logged_in and self.user.favorites:
            if item.type == 'ALBUM':
                item._isFavorite = self.user.favorites.isFavoriteAlbum(item.id)
            elif item.type == 'PLAYLIST':
                item._isFavorite = self.user.favorites.isFavoritePlaylist(item.id)
            elif item.type == 'VIDEO':
                item._isFavorite = self.user.favorites.isFavoriteVideo(item.id)
        return item

    def _parse_track(self, json_obj):
        track = Track(**json_obj)
        if 'artist' in json_obj:
            track.artist = self._parse_artist(json_obj['artist'])
        elif 'artists' in json_obj:
            track.artist = self._parse_artist(json_obj['artists'][0])
        if 'artists' in json_obj:
            track.artists, track._ftArtists = self._parse_all_artists(track.artist.id, json_obj['artists'])
        else:
            track.artists = [track.artist]
            track._ftArtists = []
        track.album = self._parse_album(json_obj['album'], artist=track.artist)
        if self.is_logged_in and self.user.favorites:
            track._isFavorite = self.user.favorites.isFavoriteTrack(track.id)
        return track

    def _parse_video(self, json_obj):
        video = Video(**json_obj)
        if 'artist' in json_obj:
            video.artist = self._parse_artist(json_obj['artist'])
        elif 'artists' in json_obj:
            video.artist = self._parse_artist(json_obj['artists'][0])
        if 'artists' in json_obj:
            video.artists, video._ftArtists = self._parse_all_artists(video.artist.id, json_obj['artists'])
            if not 'artist' in json_obj and len(video.artists) > 0:
                video.artist = video.artists[0]
        else:
            video.artists = [video.artist]
            video._ftArtists = []
        if self.is_logged_in and self.user.favorites:
            video._isFavorite = self.user.favorites.isFavoriteVideo(video.id)
        return video

    def _parse_category(self, json_obj):
        return Category(**json_obj)

    def _parse_search(self, json_obj):
        result = SearchResult()
        if 'artists' in json_obj:
            result.artists = [self._parse_artist(json) for json in json_obj['artists']['items']]
        if 'albums' in json_obj:
            result.albums = [self._parse_album(json) for json in json_obj['albums']['items']]
        if 'tracks' in json_obj:
            result.tracks = [self._parse_track(json) for json in json_obj['tracks']['items']]
        if 'playlists' in json_obj:
            result.playlists = [self._parse_playlist(json) for json in json_obj['playlists']['items']]
        if 'videos' in json_obj:
            result.videos = [self._parse_video(json) for json in json_obj['videos']['items']]
        return result

#------------------------------------------------------------------------------
# Class to work with user favorites
#------------------------------------------------------------------------------

class Favorites(object):

    ids_loaded = False
    ids = {}

    def __init__(self, session, user_id):
        self._session = session
        self._base_url = 'users/%s/favorites' % user_id
        self.reset()

    def reset(self):
        self.ids_loaded = False
        self.ids = {'artists': [], 'albums': [], 'playlists': [], 'tracks': [], 'videos': []}

    def load_all(self, force_reload=False):
        if force_reload or not self.ids_loaded:
            # Reset all first
            self.ids = {'artists': [], 'albums': [], 'playlists': [], 'tracks': [], 'videos': []}
            self.ids_loaded = False
            r = self._session.request('GET', self._base_url + '/ids')
            if r.ok:
                json_obj = r.json()
                if 'ARTIST' in json_obj:
                    self.ids['artists'] = json_obj.get('ARTIST')
                if 'ALBUM' in json_obj:
                    self.ids['albums'] = json_obj.get('ALBUM')
                if 'PLAYLIST' in json_obj:
                    self.ids['playlists'] = json_obj.get('PLAYLIST')
                if 'TRACK' in json_obj:
                    self.ids['tracks'] = json_obj.get('TRACK')
                if 'VIDEO' in json_obj:
                    self.ids['videos'] = json_obj.get('VIDEO')
                self.ids_loaded = True
        return self.ids

    def get(self, content_type, limit=9999):
        items = self._session._map_request(self._base_url + '/%s' % content_type, params={'limit': limit if content_type <> 'videos' else min(limit, 100)}, ret=content_type)
        self.ids[content_type] = ['%s' % item.id for item in items]
        return items

    def add(self, content_type, item_ids):
        if isinstance(item_ids, basestring):
            ids = [item_ids]
        else:
            ids = item_ids
        param = {'artists': 'artistId', 'albums': 'albumId', 'playlists': 'uuid', 
                 'tracks': 'trackIds', 'videos': 'videoIds'}.get(content_type)
        ok = self._session.request('POST', self._base_url + '/%s' % content_type, data={param: ','.join(ids)}).ok
        if ok and self.ids_loaded:
            for _id in ids:
                if _id not in self.ids[content_type]:
                    self.ids[content_type].append(_id)
        return ok

    def remove(self, content_type, item_id):
        ok = self._session.request('DELETE', self._base_url + '/%s/%s' % (content_type, item_id)).ok
        if ok and self.ids_loaded and item_id in self.ids.get(content_type, []):
            self.ids[content_type].remove(item_id)
        return ok

    def add_artist(self, artist_id):
        return self.add('artists', artist_id)

    def remove_artist(self, artist_id):
        return self.remove('artists', artist_id)

    def add_album(self, album_id):
        return self.add('albums', album_id)

    def remove_album(self, album_id):
        return self.remove('albums', album_id)

    def add_playlist(self, playlist_id):
        return self.add('playlists', playlist_id)

    def remove_playlist(self, playlist_id):
        return self.remove('playlists', playlist_id)

    def add_track(self, track_id):
        return self.add('tracks', track_id)

    def remove_track(self, track_id):
        return self.remove('tracks', track_id)

    def add_video(self, video_id):
        return self.add('videos', video_id)

    def remove_video(self, video_id):
        return self.remove('videos', video_id)

    def artists(self):
        return self.get('artists')

    def isFavoriteArtist(self, artist_id):
        return '%s' % artist_id in self.ids.get('artists', [])

    def albums(self):
        return self.get('albums')

    def isFavoriteAlbum(self, album_id):
        return '%s' % album_id in self.ids.get('albums', [])

    def playlists(self):
        return self.get('playlists')

    def isFavoritePlaylist(self, playlist_id):
        return '%s' % playlist_id in self.ids.get('playlists', [])

    def tracks(self):
        return self.get('tracks')

    def isFavoriteTrack(self, track_id):
        return '%s' % track_id in self.ids.get('tracks', [])

    def videos(self):
        return self.get('videos', limit=100)

    def isFavoriteVideo(self, video_id):
        return '%s' % video_id in self.ids.get('videos', [])

#------------------------------------------------------------------------------
# Class to work with users playlists
#------------------------------------------------------------------------------

class User(object):

    subscription = None
    favorites = None

    def __init__(self, session, user_id, subscription_type=SubscriptionType.hifi):
        self._session = session
        self.id = user_id
        self._base_url = 'users/%s' % user_id
        self.favorites = Favorites(session, user_id)
        self.subscription = Subscription(subscription = {'type': subscription_type})

    def playlists(self, offset=0, limit=9999):
        return self._session._map_request(self._base_url + '/playlists', params={'offset': offset, 'limit': limit}, ret='playlists')

    def create_playlist(self, title, description=''):
        return self._session._map_request(self._base_url + '/playlists', method='POST', data={'title': title, 'description': description}, ret='playlist')

    def delete_playlist(self, playlist_id):
        return self._session.request('DELETE', 'playlists/%s' % playlist_id).ok

    def rename_playlist(self, playlist, title, description=''):
        if not isinstance(playlist, Playlist):
            playlist = self._session.get_playlist(playlist)
        ok = False
        if not playlist._etag:
            # Read Playlist to get ETag
            playlist = self._session.get_playlist(playlist.id)
        if playlist and playlist._etag:
            headers = {'If-None-Match': '%s' % playlist._etag}
            data = {'title': title, 'description': description}
            ok = self._session.request('POST', 'playlists/%s' % playlist.id, data=data, headers=headers).ok
        else:
            log.debug('Got no ETag for playlist %s' & playlist.title)
        return ok

    def add_playlist_entries(self, playlist=None, item_ids=[]):
        if not isinstance(playlist, Playlist):
            playlist = self._session.get_playlist(playlist)
        ok = False
        trackIds = ','.join(item_ids)
        if not playlist._etag:
            # Read Playlist to get ETag
            playlist = self._session.get_playlist(playlist.id)
        if playlist and playlist._etag:
            headers = {'If-None-Match': '%s' % playlist._etag}
            data = {'trackIds': trackIds, 'toIndex': playlist.numberOfItems}
            ok = self._session.request('POST', 'playlists/%s/tracks' % playlist.id, data=data, headers=headers).ok
        else:
            log.debug('Got no ETag for playlist %s' & playlist.title)
        return ok

    def remove_playlist_entry(self, playlist_id, entry_no=None, item_id=None):
        if item_id:
            # Got Track/Video-ID to remove from Playlist
            entry_no = None
            items = self._session.get_playlist_items(playlist_id)
            for item in items:
                if str(item.id) == str(item_id):
                    entry_no = item._playlist_pos
            if entry_no == None:
                return False
        # Read Playlist to get ETag
        playlist = self._session.get_playlist(playlist_id)
        ok = False
        if playlist and playlist._etag:
            headers = {'If-None-Match': '%s' % playlist._etag}
            ok = self._session.request('DELETE', 'playlists/%s/tracks/%s' % (playlist_id, entry_no), headers=headers).ok
        return ok
