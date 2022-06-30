# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2022 morguldir
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

from __future__ import print_function

import requests
import pytest
import tidalapi
from tidalapi import Artist, Album, Playlist, Track, Video


def test_load_oauth_session(session):
    token_type = session.token_type
    access_token = session.access_token
    expiry_time = session.expiry_time
    session = tidalapi.Session()
    assert session.load_oauth_session(token_type, access_token, expiry_time)
    assert session.check_login()
    assert isinstance(session.user, tidalapi.LoggedInUser)


def test_failed_login():
    session = tidalapi.Session()
    with pytest.raises(requests.HTTPError):
        session.login("", "")
    assert session.check_login() is False


@pytest.mark.interactive
def test_oauth_login(capsys):
    config = tidalapi.Config(item_limit=20000)
    session = tidalapi.Session(config)
    login, future = session.login_oauth()
    with capsys.disabled():
        print("Visit", login.verification_uri_complete, "to log in, the link expires in", login.expires_in, "seconds")
    future.result()
    assert session.check_login()
    assert session.config.item_limit == 10000


def test_failed_oauth_login(session):
    client_id = session.config.client_id
    config = tidalapi.Config()
    config.client_id = client_id + 's'
    session = tidalapi.Session(config)
    with pytest.raises(requests.HTTPError):
        session.login_oauth()


@pytest.mark.interactive
def test_oauth_login_simple(capsys):
    session = tidalapi.Session()
    with capsys.disabled():
        session.login_oauth_simple()


def test_oauth_refresh(session):
    access_token = session.access_token
    expiry_time = session.expiry_time
    refresh_token = session.refresh_token
    session.token_refresh(refresh_token)
    assert session.access_token != access_token
    assert session.expiry_time != expiry_time


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

    assert (search['top_hit']).name == "Walker Hayes"


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
    assert session.config.quality == tidalapi.Quality.master.value
    assert session.config.video_quality == tidalapi.VideoQuality.high.value
    assert session.config.alac is True
