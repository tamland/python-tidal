# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 morguldir
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

@pytest.fixture(scope='session')
def session():
    session = tidalapi.Session()
    username = os.getenv("TIDAL_USERNAME")
    password = os.getenv("TIDAL_PASSWORD")
    session.login(username, password)
    return session

def test_get_artist(session):
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

def test_get_artist_videos(session):
    videos = session.get_artist_videos(3502112)
    assert any([v.name == 'Call on Me' for v in videos])

def test_get_album(session):
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
    assert tracks[0].artist.name == 'Lasgo'
    assert tracks[0].album.name == 'Smile'
    assert tracks[-1].name == 'Gone'
    assert tracks[-1].track_num == 13
    assert tracks[-1].duration == 210
    assert tracks[-1].version == 'Acoustic Version'

def test_get_album_videos(session):
    videos = session.get_album_videos(108046179)
    assert videos[0].name == 'Formation (Choreography Version)'
    assert videos[0].track_num == 14
    assert videos[0].duration == 262
    assert videos[0].artist.name == 'Beyoncé'
    assert videos[0].album.name == 'Lemonade'
    assert videos[1].name == 'Lemonade Film'
    assert videos[1].track_num == 15
    assert videos[1].duration == 3955

def test_get_album_items(session):
    items = session.get_album_items(108046179)
    assert items[0].name == 'Pray You Catch Me'
    assert items[0].track_num == 1
    assert items[0].duration == 196
    assert items[0].artist.name == 'Beyoncé'
    assert items[0].album.name == 'Lemonade'
    assert items[-1].name == 'Lemonade Film'
    assert items[-1].track_num == 15
    assert items[-1].duration == 3955
    assert items[-1].type == 'Music Video'

def test_artist_radio(session):
    tracks = session.get_artist_radio(16147)
    assert tracks

def test_search(session):
    res = session.search('artist', 'lasgo')
    assert res.artists[0].name == "Lasgo"

def test_artist_picture(session):
    artist = session.get_artist(16147)
    assert requests.get(artist.picture(640,640)).status_code == 200
    assert requests.get(tidalapi.models.Artist.image.fget(artist, 640, 640)).status_code == 200

def test_album_picture(session):
    album = session.get_album(17925106)
    assert requests.get(album.picture(640, 640)).status_code == 200
    assert requests.get(tidalapi.models.Album.image.fget(album, 640, 640)).status_code == 200

def test_playlist_picture(session):
    playlist = session.get_playlist('33136f5a-d93a-4469-9353-8365897aaf94')
    assert requests.get(playlist.picture(750, 750)).status_code == 200
    assert requests.get(tidalapi.models.Playlist.image.fget(playlist, 750, 750)).status_code == 200

def test_get_track_url(session):
    track = session.get_track(108043415)
    session.get_track_url(track.id)

def test_get_video_url(session):
    video = session.get_video(108046194)
    session.get_video_url(video.id)

def test_load_session(session):
    """
    Test loading a session from a session id without supplying country code and user_id
    """
    user_id = session.user.id
    country_code = session.country_code
    session_id = session.session_id
    session = tidalapi.Session()
    session.load_session(session_id)
    assert user_id == session.user.id
    assert country_code == session.country_code
