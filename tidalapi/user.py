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

"""
A module containing classes and functions related to tidal users.

:class:`User` is a class with user information.
:class:`Favorites` is class with a users favorites.
"""

from copy import copy
import dateutil.parser


class User(object):
    """
    A class containing various information about a TIDAL user.

    The attributes of this class are pretty varied. ID is the only attribute you can rely on being set.
    If you initialized a specific user, you will get id, first_name, last_name, and picture_id.
    If parsed as a playlist creator, you will get an ID and a name, if the creator isn't an artist, name will be 'user'.
    If the parsed user is the one logged in, for example in session.user, you will get the remaining attributes, and id.
    """
    id = -1

    def __init__(self, session, user_id):
        self.id = user_id
        self.session = session
        self.request = session.request
        self.playlist = session.playlist()

    def factory(self):
        return self.request.map_request('users/%s' % self.id, parse=self.parse)

    def parse(self, json_obj):

        if 'username' in json_obj:
            user = LoggedInUser(self.session, json_obj['id'])

        elif 'firstName' in json_obj:
            user = FetchedUser(self.session, json_obj['id'])

        elif json_obj:
            user = PlaylistCreator(self.session, json_obj['id'])

        # When searching TIDAL does not show up as a creator in the json data.
        else:
            user = PlaylistCreator(self.session, 0)

        return user.parse(json_obj)


class FetchedUser(User):
    first_name = None
    last_name = None
    picture_id = None

    def parse(self, json_obj):
        self.id = json_obj['id']
        self.first_name = json_obj['firstName']
        self.last_name = json_obj['lastName']
        self.picture_id = json_obj['picture']

        return copy(self)

    def image(self, dimensions):
        if dimensions not in [100, 210, 600]:
            raise ValueError("Invalid resolution {0} x {0}".format(dimensions))

        return self.session.config.image_url % (self.picture_id.replace('-', '/'), dimensions, dimensions)


class LoggedInUser(FetchedUser):
    username = None
    email = None
    created = None
    newsletter = None
    accepted_eula = None
    gender = None
    date_of_birth = None
    facebook_uid = None
    apple_uid = None

    def __init__(self, session, user_id):
        super(LoggedInUser, self).__init__(session, user_id)
        self.favorites = Favorites(session, self.id)

    def parse(self, json_obj):
        super(LoggedInUser, self).parse(json_obj)
        self.username = json_obj['username']
        self.email = json_obj['email']
        self.created = dateutil.parser.isoparse(json_obj['created'])
        self.newsletter = json_obj['newsletter']
        self.accepted_eula = json_obj['acceptedEULA']
        self.gender = json_obj['gender']
        self.date_of_birth = json_obj['dateOfBirth']
        self.facebook_uid = json_obj['facebookUid']
        self.apple_uid = json_obj['appleUid']

        return copy(self)

    def playlists(self):
        """
        Get the playlists created by the user.

        :return: Returns a list of :class:`~tidalapi.playlist.Playlist` objects containing the playlists.
        """
        return self.request.map_request('users/%s/playlists' % self.id, parse=self.playlist.parse)

    def create_playlist(self, title, description):
        data = {'title': title, 'description': description}
        json = self.request.request('POST', 'users/%s/playlists' % self.id, data=data).json()
        playlist = self.session.playlist().parse(json)
        return playlist.factory()


class PlaylistCreator(User):
    name = None

    def parse(self, json_obj):
        if self.id == 0:
            self.name = "TIDAL"

        elif 'name' in json_obj:
            self.name = json_obj['name']

        elif self.id == self.session.user.id:
            self.name = "me"

        else:
            self.name = "user"

        return copy(self)


class Favorites(object):
    """
    An object containing a users favourites.
    """
    def __init__(self, session, user_id):
        self.session = session
        self.requests = session.request
        self.base_url = 'users/%s/favorites' % user_id

    def add_album(self, album_id):
        """
        Adds an album to the users favorites.

        :param album_id: TIDAL's identifier of the album.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request('POST', self.base_url + '/albums', data={'albumId': album_id}).ok

    def add_artist(self, artist_id):
        """
        Adds an artist to the users favorites.

        :param artist_id: TIDAL's identifier of the artist
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request('POST', self.base_url + '/artists', data={'artistId': artist_id}).ok

    def add_playlist(self, playlist_id):
        """
        Adds a playlist to the users favorites.

        :param playlist_id:  TIDAL's identifier of the playlist.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request('POST', self.base_url + '/playlists', data={'uuids': playlist_id}).ok

    def add_track(self, track_id):
        """
        Adds a track to the users favorites.

        :param track_id: TIDAL's identifier of the track.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request('POST', self.base_url + '/tracks', data={'trackId': track_id}).ok

    def add_video(self, video_id):
        """
        Adds a video to the users favorites.

        :param video_id: TIDAL's identifier of the video.
        :return: A boolean indicating whether the request was successful or not.
        """
        params = {'limit': '100'}
        return self.requests.request('POST', self.base_url + '/videos', data={'videoIds': video_id}, params=params).ok

    def remove_artist(self, artist_id):
        """
        Removes a track from the users favorites.

        :param artist_id: TIDAL's identifier of the artist.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request('DELETE', self.base_url + '/artists/%s' % artist_id).ok

    def remove_album(self, album_id):
        """
        Removes an album from the users favorites.

        :param album_id: TIDAL's identifier of the album
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request('DELETE', self.base_url + '/albums/%s' % album_id).ok

    def remove_playlist(self, playlist_id):
        """
        Removes a playlist from the users favorites.

        :param playlist_id: TIDAL's identifier of the playlist.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request('DELETE', self.base_url + '/playlists/%s' % playlist_id).ok

    def remove_track(self, track_id):
        """
        Removes a track from the users favorites.

        :param track_id: TIDAL's identifier of the track.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request('DELETE', self.base_url + '/tracks/%s' % track_id).ok

    def remove_video(self, video_id):
        """
        Removes a video from the users favorites.

        :param video_id: TIDAL's identifier of the video.
        :return: A boolean indicating whether the request was successful or not.

        """
        return self.requests.request('DELETE', self.base_url + '/videos/%s' % video_id).ok

    def artists(self, limit=None, offset=0):
        """
        Get the users favorite artists

        :return: A :class:`list` of :class:`~tidalapi.artist.Artist` objects containing the favorite artists.
        """
        params = {'limit': limit, 'offset': offset}
        return self.requests.map_request(self.base_url + '/artists', params=params, parse=self.session.parse_artist)

    def albums(self, limit=None, offset=0):
        """
        Get the users favorite albums

        :return: A :class:`list` of :class:`~tidalapi.album.Album` objects containing the favorite albums.
        """
        params = {'limit': limit, 'offset': offset}
        return self.requests.map_request(self.base_url + '/albums', params=params, parse=self.session.parse_album)

    def playlists(self, limit=None, offset=0):
        """
        Get the users favorite playlists

        :return: A :class:`list` :class:`~tidalapi.playlist.Playlist` objects containing the favorite playlists.
        """
        params = {'limit': limit, 'offset': offset}
        return self.requests.map_request(self.base_url + '/playlists', params=params, parse=self.session.parse_playlist)

    def tracks(self, limit=None, offset=0):
        """
        Get the users favorite tracks

        :return: A :class:`list` of :class:`~tidalapi.track.Track` objects containing all of the favorite tracks.
        """
        params = {'limit': limit, 'offset': offset}
        return self.requests.map_request(self.base_url + '/tracks', params=params, parse=self.session.parse_track)

    def videos(self):
        """
        Get the users favorite videos

        :return: A :class:`list` of :class:`~tidalapi.media.Video` objects containing all the favorite videos
        """
        return self.requests.get_items(self.base_url + '/videos', parse=self.session.parse_media)
