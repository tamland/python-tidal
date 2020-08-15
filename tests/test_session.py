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

import requests
import pytest
import tidalapi
from tidalapi import Artist, Album, Playlist, Track, Video
from .conftest import get_credentials


def test_load_session(session):
    session_id = session.session_id
    session = tidalapi.Session()
    assert session.load_session(session_id)
    assert session.check_login()
    assert isinstance(session.user, tidalapi.LoggedInUser)
    assert session.load_session(session_id + "f") is False


def test_failed_login():
    session = tidalapi.Session()
    with pytest.raises(requests.HTTPError):
        session.login("", "")
    assert session.check_login() is False


def test_revoked_token():
    username, password = get_credentials()

    config = tidalapi.Config(alac=True)
    config.api_token = "MbjR4DLXz1ghC4rV"
    session = tidalapi.Session(config)
    session.login(username, password)
    assert session.config.alac is False


def test_login():
    username, password = get_credentials()

    # Verify that our revoked token detection isn't interfering with normal usage
    # Also let's us know if any of the tokens have been revoked.
    # Set the item limit so we can test limiting it to 10000.
    config = tidalapi.Config(alac=False, item_limit=20000)
    session = tidalapi.Session(config)
    session.login(username, password)
    assert session.config.alac is False
    assert session.config.item_limit == 10000

    # Go back to the ALAC token so we can use videos.
    config = tidalapi.Config(alac=True)
    session = tidalapi.Session(config)
    session.login(username, password)
    assert session.config.alac is True


def test_search(session):
    # Great edge case test
    search = session.search("Walker", limit=300)
    assert len(search['artists']) == 300
    assert len(search['albums']) == 300
    assert len(search['tracks']) == 300
    assert len(search['videos']) == 300
    assert len(search['playlists']) >= 195
    assert isinstance(search['artists'][0], Artist)
    assert isinstance(search['albums'][0], Album)
    assert isinstance(search['tracks'][0], Track)
    assert isinstance(search['videos'][0], Video)
    assert isinstance(search['playlists'][0], Playlist)

    assert (search['top_hit']).name == "Alan Walker"


def test_type_search(session):
    search = session.search("Hello", [Playlist, Video])
    assert isinstance(search['top_hit'], Playlist)

    assert len(search['artists']) == 0
    assert len(search['albums']) == 0
    assert len(search['tracks']) == 0
    assert len(search['videos']) == 50
    assert len(search['playlists']) == 50


def test_invalid_type_search(session):
    with pytest.raises(ValueError):
        session.search("Hello", [tidalapi.Genre])


def test_invalid_search(session):
    search = session.search('ERIWGJRGIJGRWEIOGRJOGREIWJIOWREG')
    assert len(search['artists']) == 0
    assert len(search['albums']) == 0
    assert len(search['tracks']) == 0
    assert len(search['videos']) == 0
    assert len(search['playlists']) == 0
    assert search['top_hit'] is None


def test_config(session):
    assert session.config.item_limit == 1000
    assert session.config.quality == tidalapi.Quality.lossless.value
    assert session.config.video_quality == tidalapi.VideoQuality.high.value
    assert session.config.alac is True
