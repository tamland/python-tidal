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


from __future__ import unicode_literals
from enum import Enum

IMG_URL = "https://resources.tidal.com/images/{uuid}/{width}x{height}.jpg"


class Model(object):
    id = None
    name = None
    img_uuid = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Album(Model):
    artist = None
    artists = []
    num_tracks = -1
    duration = -1
    release_date = None

    @property
    def image(self, width=1280, height=1280):
        uuid = self.img_uuid.replace('-', '/')
        return IMG_URL.format(uuid=uuid, width=width, height=height)

    def picture(self, width, height):
        """
        A url to an album picture

        :param width: pixel width, maximum 2000
        :type width: int
        :param height: pixel height, maximum 2000
        :type height: int

        Accepted sizes: 80x80, 160x160, 320x320, 640x640 and 1280x1280
        """
        uuid = self.img_uuid.replace('-', '/')
        return IMG_URL.format(uuid=uuid, width=width, height=height)


class Artist(Model):
    roles = []
    role = None

    @property
    def image(self, width=750, height=750):
        uuid = self.img_uuid.replace('-', '/')
        return IMG_URL.format(uuid=uuid, width=width, height=height)

    def picture(self, width, height):
        """
        A url to an artist picture

        :param width: pixel width, maximum 750
        :type width: int
        :param height: pixel height, maximum 750
        :type height: int

        Accepted sizes: 80x80, 160x160, 320x320, 480x480, 750x750
        """
        uuid = self.img_uuid.replace('-', '/')
        return IMG_URL.format(uuid=uuid, width=width, height=height)


class Playlist(Model):
    description = None
    creator = None
    type = None
    is_public = None
    created = None
    last_updated = None
    num_tracks = -1
    duration = -1

    @property
    def image(self, width=1080, height=1080):
        uuid = self.img_uuid.replace('-', '/')
        return IMG_URL.format(uuid=uuid, width=width, height=height)

    def picture(self, width, height):
        """
        A url to a playlist picture

        :param width: pixel width, maximum 1080
        :type width: int
        :param height: pixel height, maximum 1080
        :type height: int

        Accepted sizes: 160x160, 320x320, 480x480, 640x640, 750x750, 1080x1080

        """
        uuid = self.img_uuid.replace('-', '/')
        return IMG_URL.format(uuid=uuid, width=width, height=height)


class Media(Model):
    duration = -1
    track_num = -1
    disc_num = 1
    version = None
    popularity = -1
    artist = None
    artists = []
    album = None
    available = True


class Track(Media):
    pass


class Video(Media):
    type = None


class SearchResult(Model):
    artists = []
    albums = []
    tracks = []
    playlists = []


class Category(Model):
    image = None


class Role(Enum):
    main = 'MAIN'
    featured = 'FEATURED'
    contributor = 'CONTRIBUTOR'
    artist = 'ARTIST'
