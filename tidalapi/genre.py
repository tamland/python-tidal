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

"""

import copy


class Genre(object):
    """

    """

    name = ""
    path = ""
    playlists = False
    artists = False
    albums = False
    tracks = False
    videos = False
    image = ""

    def __init__(self, session):
        self.session = session
        self.requests = session.request

    def parse_genre(self, json_obj):
        self.name = json_obj['name']
        self.path = json_obj['path']
        self.playlists = json_obj['hasPlaylists']
        self.artists = json_obj['hasArtists']
        self.albums = json_obj['hasAlbums']
        self.tracks = json_obj['hasTracks']
        self.videos = json_obj['hasVideos']
        self.image = "http://resources.wimpmusic.com/images/%s/460x306.jpg" % json_obj['image'].replace('-', '/')

        return copy.copy(self)

    def parse_genres(self, json_obj):
        return list(map(self.parse_genre, json_obj))

    def get_genres(self):
        return self.parse_genres(self.requests.request('GET', 'genres').json())

    def items(self, model):
        """
        Gets the current genre's items of the specified type
        :param model: The tidalapi model you want returned. See :class:`Genre`
        :return:
        """
        type_index = self.session.type_conversions['type'].index(model)
        name = self.session.type_conversions['identifier'][type_index]
        parse = self.session.type_conversions['parse'][type_index]
        if getattr(self, name):
            location = 'genres/{0}/{1}'.format(self.path, name)
            return self.requests.map_request(location, parse=parse)
        raise TypeError("This genre does not contain {0}".format(name))
