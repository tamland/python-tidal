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
import logging
import pytest
import requests
import wimpy

logging.basicConfig(level=logging.DEBUG)

@pytest.fixture()
def session():
    return wimpy.Session()

def test_artist(session):
    artist_id = 18888
    artist = session.get_artist(artist_id)
    assert artist.id == artist_id
    assert artist.name == 'Mala'

def test_get_artist_albums(session):
    albums = session.get_artist_albums(18888)
    assert albums[0].name == 'Mala in Cuba'

def test_get_artist_albums_ep_single(session):
    albums = session.get_artist_albums_ep_singles(18888)
    assert albums[0].name == 'Changes (Distance Remix) / Miracles (Commodo Remix)'

def test_get_artist_albums_other(session):
    albums = session.get_artist_albums_other(18888)
    assert albums[0].name == 'Hyperdub 10.1'

def test_album(session):
    album_id = 16909093
    album = session.get_album(album_id)
    assert album.id == album_id
    assert album.name == 'Mala in Cuba'
    assert album.num_tracks == 14
    assert album.duration == 3437
    assert album.artist.name == 'Mala'

def test_get_album_tracks(session):
    tracks = session.get_album_tracks(16909093)
    assert tracks[0].name == 'Introduction'
    assert tracks[0].track_num == 1
    assert tracks[0].duration == 155
    assert tracks[-1].name == 'Noche Sueños'
    assert tracks[-1].track_num == 14
    assert tracks[-1].duration == 338
    assert tracks[0].artist.name == 'Mala'
    assert tracks[0].album.name == 'Mala in Cuba'

def test_artist_radio(session):
    tracks = session.get_artist_radio(18888)
    assert len(tracks) > 0

def test_search(session):
    artists = session.search('artists', 'mala')
    assert artists[0].name == "Mala"

def test_artist_image(session):
    artist = session.get_artist(18888)
    assert requests.get(artist.image).status_code == 200

def test_album_image(session):
    artist = session.get_album(16909093)
    assert requests.get(artist.image).status_code == 200

def test_playlist_image(session):
    playlist = session.get_playlist('6e0791c8-cfaf-4b05-b78c-6198148413f')
    assert requests.get(playlist.image).status_code == 200
