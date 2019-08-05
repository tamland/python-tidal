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
import logging
import os
import pytest
import requests
import tidalapi

logging.basicConfig(level=logging.DEBUG)

@pytest.fixture()
def session():
    session = tidalapi.Session()
    username = os.getenv("TIDAL_USERNAME")
    password = os.getenv("TIDAL_PASSWORD")
    session.login(username, password)
    return session

def test_artist(session):
    artist_id = 16147
    artist = session.get_artist(artist_id)
    assert artist.id == artist_id
    assert artist.name == 'Lasgo'

def test_get_artist_albums(session):
    albums = session.get_artist_albums(16147)
    assert albums[0].name == 'Some Things'

def test_get_artist_albums_ep_single(session):
    albums = session.get_artist_albums_ep_singles(16147)
    assert any([a.name == 'Feeling Alive' for a in albums])

def test_get_artist_albums_other(session):
    albums = session.get_artist_albums_other(16147)
    assert any([a.name == 'Dance History 1.0' for a in albums])

def test_album(session):
    album_id = 17927863
    album = session.get_album(album_id)
    assert album.id == album_id
    assert album.name == 'Some Things'
    assert album.num_tracks == 22
    assert album.num_discs == 2
    assert album.duration == 6704
    assert album.artist.name == 'Lasgo'
    assert album.artists[0].name == 'Lasgo'

def test_get_album_tracks(session):
    tracks = session.get_album_tracks(17925106)
    assert tracks[0].name == 'Take-Off'
    assert tracks[0].track_num == 1
    assert tracks[0].duration == 56
    assert tracks[-1].name == 'Gone'
    assert tracks[-1].track_num == 13
    assert tracks[-1].duration == 210
    assert tracks[0].artist.name == 'Lasgo'
    assert tracks[0].album.name == 'Smile'

def test_artist_radio(session):
    tracks = session.get_artist_radio(16147)
    assert tracks

def test_search(session):
    res = session.search('artist', 'lasgo')
    assert res.artists[0].name == "Lasgo"

def test_artist_image(session):
    artist = session.get_artist(16147)
    assert requests.get(artist.image).status_code == 200

def test_album_image(session):
    artist = session.get_album(17925106)
    assert requests.get(artist.image).status_code == 200

def test_playlist_image(session):
    playlist = session.get_playlist('33136f5a-d93a-4469-9353-8365897aaf94')
    assert requests.get(playlist.image).status_code == 200
