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
A module containing things related to TIDAL playlists.
"""

import copy
import dateutil.parser


class Playlist(object):
    """
    An object containing various data about a playlist and methods to work with them.
    """

    id = None
    name = None
    num_tracks = -1
    num_videos = -1
    creator = None
    description = None
    duration = -1
    last_updated = None
    created = None
    type = None
    public = False
    popularity = -1
    promoted_artists = None
    last_item_added_at = None
    picture = None
    square_picture = None
    _etag = None

    def __init__(self, session, playlist_id):
        self.id = playlist_id
        self.session = session
        self.requests = session.request
        self._base_url = 'playlists/%s'
        if playlist_id:
            request = self.requests.request('GET', self._base_url % playlist_id)
            self._etag = request.headers['etag']
            self.parse(request.json())

    def parse(self, json_obj):
        """
        Parses a playlist from tidal, replaces the current playlist object.

        :param json_obj: Json data returned from api.tidal.com containing a playlist
        :return: Returns a copy of the original :exc:'Playlist': object
        """
        self.id = json_obj['uuid']
        self.name = json_obj['title']
        self.num_tracks = int(json_obj['numberOfTracks'])
        self.num_videos = int(json_obj['numberOfVideos'])
        self.description = json_obj['description']
        self.duration = int(json_obj['duration'])
        self.last_updated = dateutil.parser.isoparse(json_obj['lastUpdated'])
        self.created = dateutil.parser.isoparse(json_obj['created'])
        self.type = json_obj['type']
        self.public = bool(json_obj['publicPlaylist'])
        self.popularity = json_obj['popularity']

        if self.type == 'ARTIST' and json_obj['creator'].get('id') != 0:
            self.creator = self.session.parse_artist(json_obj['creator'])
        else:
            self.creator = self.session.parse_user(json_obj['creator'])

        self.picture = json_obj['image']
        self.square_picture = json_obj['squareImage']

        promoted_artists = json_obj['promotedArtists']
        if promoted_artists:
            self.promoted_artists = self.session.parse_artists(promoted_artists)

        last_item_added_at = json_obj.get('lastItemAddedAt')
        if last_item_added_at:
            self.last_item_added_at = dateutil.parser.isoparse(last_item_added_at)

        return copy.copy(self)

    def factory(self):
        if self.creator and self.creator.id == self.session.user.id:
            return UserPlaylist(self.session, self.id)

        return self

    def tracks(self, limit=None, offset=0):
        """
        Gets the playlists̈́' tracks from TIDAL.

        :param limit: The amount of items you want returned.
        :param offset: The index of the first item you want included.
        :return: A list of :class:`Tracks <.Track>`
        """
        params = {'limit': limit, 'offset': offset}
        request = self.requests.request('GET', self._base_url % self.id + '/tracks', params=params)
        self._etag = request.headers['etag']
        return self.requests.map_json(json_obj=request.json(), parse=self.session.parse_track)

    def items(self, limit=100, offset=0):
        """
        Fetches up to the first 100 items, including tracks and videos

        :param limit: The amount of items you want, up to 100.
        :param offset: The index of the first item you want returned
        :return: A list of :class:`Tracks<.Track>` and :class:`Videos<.Video>`
        """
        params = {'limit': limit, 'offset': offset}
        request = self.requests.request('GET', self._base_url % self.id + '/items', params=params)
        self._etag = request.headers['etag']
        return self.requests.map_json(request.json(), parse=self.session.parse_media)

    def image(self, dimensions):
        """
        A URL to a playlist picture

        :param dimensions: The width and height that want from the image
        :type dimensions: int
        :return: A url to the image

        Original sizes: 160x160, 320x320, 480x480, 640x640, 750x750, 1080x1080
        """

        if dimensions not in [160, 320, 480, 640, 750, 1080]:
            raise ValueError("Invalid resolution {0} x {0}".format(dimensions))

        return self.session.config.image_url % (self.square_picture.replace('-', '/'), dimensions, dimensions)

    def wide_image(self, width=1080, height=720):
        """
        Create a url to a wider playlist image.


        :param width: The width of the image
        :param height: The height of the image
        :return: Returns a url to the image with the specified resolution

        Valid sizes: 160x107, 480x320, 750x500, 1080x720
        """

        if (width, height) not in [(160, 107), (480, 320), (750, 500), (1080, 720)]:
            raise ValueError("Invalid resolution {} x {}".format(width, height))

        return self.session.config.image_url % (self.picture.replace('-', '/'), width, height)


class UserPlaylist(Playlist):
    def _reparse(self):
        request = self.requests.request('GET', self._base_url % self.id)
        self._etag = request.headers['etag']
        self.requests.map_json(request.json(), parse=self.parse)

    def edit(self, title=None, description=None):
        if not title:
            title = self.name
        if not description:
            description = self.description

        data = {'title': title, 'description': description}
        self.requests.request('POST', self._base_url % self.id, data=data)

    def delete(self):
        self.requests.request('DELETE', self._base_url % self.id)

    def add(self, media_ids):
        data = {'onDupes': 'SKIP', 'trackIds': ','.join(map(str, media_ids))}
        params = {'limit': 100}
        headers = {'If-None-Match': self._etag}
        self.requests.request('POST', self._base_url % self.id + '/items', params=params, data=data, headers=headers)
        self._reparse()

    def remove_by_index(self, index):
        headers = {'If-None-Match': self._etag}
        self.requests.request('DELETE', (self._base_url + '/items/%i') % (self.id, index), headers=headers)

    def _calculate_id(self, media_id):
        i = 0
        while i < self.num_tracks:
            items = self.items(100, i)
            for index, item in enumerate(items):
                if item.id == media_id:
                    # Return the amount of items we have gone through plus the index in the last list.
                    return index + i

            i += len(items)

    def remove_by_id(self, media_id):
        index = self._calculate_id(media_id)
        self.remove_by_index(index)
