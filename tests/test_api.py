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
import pytest
import requests
import tidalapi

logging.basicConfig(level=logging.DEBUG)

@pytest.fixture()
def session():
    session = tidalapi.Session()
    # Trial Mode without login !
    # session.login('username', 'password')
    return session

def test_user_subscription(session):
    if session.is_logged_in:
        subs = session.get_user_subscription(session.user.id)
        assert subs.type in ['PREMIUM', 'HIFI']

def test_user_playlists(session):
    if session.is_logged_in:
        userpl = session.user.playlists()
        assert len(userpl) > 0
        tracks = session.get_playlist_items(userpl[0].id)
        assert len(tracks) > 0

def test_artist(session):
    artist_id = 18888
    artist = session.get_artist(artist_id)
    assert artist.id == artist_id
    assert artist.name == 'Mala'

def test_get_artist_albums(session):
    albums = session.get_artist_albums(18888)
    assert any([a.name == 'Mala in Cuba' for a in albums])

def test_get_artist_albums_ep_single(session):
    albums = session.get_artist_albums_ep_singles(18888)
    assert any([a.name == 'Noches Sueños' for a in albums])

def test_get_artist_albums_other(session):
    albums = session.get_artist_albums_other(18888)
    assert any([a.name == 'Hyperdub 10.1' for a in albums])

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

def test_get_artist_top(session):
    tracks = session.get_artist_top_tracks(18888)
    assert len(tracks) > 0

def test_get_artist_videos(session):
    videos = session.get_artist_videos(1566)
    assert videos[0].artist.name == 'Beyoncé'
    assert isinstance(videos[0], tidalapi.Video)
    assert any([v.name == 'LEMONADE' for v in videos])

def test_search(session):
    res = session.search('artist', 'mala')
    assert res.artists[0].name == "Mala"

def test_artist_image(session):
    artist = session.get_artist(18888)
    assert requests.get(artist.image).status_code == 200

def test_album_image(session):
    artist = session.get_album(16909093)
    assert requests.get(artist.image).status_code == 200

def test_get_playlist(session):
    playlist = session.get_playlist('56c28e48-5d09-4fb0-812e-c6c7c6647dcf')
    assert 'TIDAL' in playlist.name 
    assert playlist.numberOfItems > 0
    assert playlist.numberOfTracks > 0
    assert playlist.numberOfVideos == 0
    playlist = session.get_playlist('7ba7548e-a5d9-4387-9ba1-d8aea06d3369')
    assert playlist.numberOfItems > 0
    if session.is_logged_in:
        assert playlist.numberOfTracks == 0
        assert playlist.numberOfVideos > 0

def test_playlist_image(session):
    playlist = session.get_playlist('33136f5a-d93a-4469-9353-8365897aaf94')
    assert requests.get(playlist.image).status_code == 200

def test_get_playlist_tracks(session):
    items = session.get_playlist_tracks('56c28e48-5d09-4fb0-812e-c6c7c6647dcf')
    assert len(items) > 0
    assert isinstance(items[0], tidalapi.Track)

def test_get_playlist_items(session):
    items = session.get_playlist_tracks('7ba7548e-a5d9-4387-9ba1-d8aea06d3369')
    assert len(items) > 0
    assert isinstance(items[0], tidalapi.Track)
    items = session.get_playlist_items('7ba7548e-a5d9-4387-9ba1-d8aea06d3369')
    assert len(items) > 0
    assert isinstance(items[0], tidalapi.Video)

def test_get_genres(session):
    items = session.get_genres()
    assert len(items) > 0

def test_get_genres_items(session):
    items = session.get_genre_items('pop', 'tracks')
    assert len(items) > 0

def test_get_moods(session):
    items = session.get_moods()
    assert len(items) > 0
    assert isinstance(items[0], tidalapi.Category)

def test_get_movies(session):
    items = session.get_movies()
    assert len(items) > 0
    assert isinstance(items[0], tidalapi.Video)

def test_get_shows(session):
    items = session.get_shows()
    assert len(items) > 0
    assert isinstance(items[0], tidalapi.Playlist)

def test_get_track_url(session):
    items = session.get_category_content('featured', 'new', 'tracks', offset=0, limit=3)
    assert len(items) > 0
    url = session.get_media_url(items[0].id)
    assert url.startswith('http') or url.startswith('rtmp')

def test_get_video_url(session):
    items = session.get_category_content('featured', 'new', 'videos', offset=0, limit=3)
    assert len(items) > 0
    url = session.get_video_url(items[0].id)
    assert url.startswith('http') or url.startswith('rtmp')

def test_offset(session):
    items1 = session.get_category_content('featured', 'new', 'tracks', offset=0, limit=30)
    assert len(items1) == 30
    items2 = session.get_category_content('featured', 'new', 'tracks', offset=10, limit=10)
    assert len(items2) == 10
    assert items1[10].id == items2[0].id
    assert items1[19].id == items2[9].id
