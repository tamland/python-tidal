# -*- coding: utf-8 -*-
#
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

from io import BytesIO
from PIL import Image
import pytest
import tidalapi


def test_get_genres(session):
    genres = list(session.genre.get_genres())
    assert 'Jazz' in [genre.name for genre in genres]


def test_get_items(session):
    genres = list(session.genre.get_genres())
    genres[0].items(tidalapi.Album)
    with pytest.raises(TypeError):
        genres[0].items(tidalapi.Artist)
    genres[0].items(tidalapi.Track)
    genres[0].items(tidalapi.Video)
    genres[0].items(tidalapi.Playlist)


def test_get_electronic_items(session):
    genres = list(session.genre.get_genres())
    electronic = [genre for genre in genres if genre.path == 'Electronic'][0]
    electronic_items = electronic.items(tidalapi.Playlist)
    assert 'Rising: Electronic' in [playlist.name for playlist in electronic_items]


def test_image(session):
    genres = session.genre.get_genres()
    electronic = [genre for genre in genres if genre.path == 'Electronic'][0]
    image = session.request_session.get(electronic.image).content
    assert Image.open(BytesIO(image)).size == (460, 306)
