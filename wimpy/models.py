# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

class Immutable(object):
    id = None
    name = None

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            self.__dict__[name] = value

    def __setattr__(self, name, value):
        raise AttributeError('immutable')


class Album(Immutable):
    artist = None
    num_tracks = -1
    duration = -1


class Artist(Immutable):
    pass


class Track(Immutable):
    duration = -1
    track_num = -1
    popularity = -1
    artist = None
    album = None
