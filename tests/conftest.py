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

import logging
import keyring
import keyring.backends
import keyring.errors
import pytest
import tidalapi


@pytest.fixture(scope='session')
def session(request):
    logging.basicConfig(level=logging.DEBUG)
    return login(request)


def login(request):
    access_token, refresh_token, expiry_time, token_type = get_credentials()
    config = tidalapi.Config(quality=tidalapi.Quality.master)
    tidal_session = tidalapi.Session(config)

    if access_token and tidal_session.load_oauth_session(token_type, access_token, refresh_token, expiry_time):
        return tidal_session

    else:
        _oauth_login(request, tidal_session)
        info = [
            tidal_session.access_token,
            tidal_session.refresh_token,
            tidal_session.token_type,
            str(tidal_session.expiry_time)
        ]
        if not isinstance(keyring.get_keyring(), keyring.backends.fail.Keyring):
            keyring.set_password('TIDAL Access Token', tidal_session.user.email, ':'.join(info))
    return tidal_session


def _oauth_login(request, tidal_session):
    login, future = tidal_session.login_oauth()
    # https://github.com/pytest-dev/pytest/issues/2704
    capmanager = request.config.pluginmanager.getplugin("capturemanager")
    with capmanager.global_and_fixture_disabled():
        print("Visit", login.verification_uri_complete, "to log in, the link expires in", login.expires_in, "seconds")
    future.result()


def get_credentials():
    """
    Attempt to get the password and username from env variables or the keyring.

    :return: Returns a tuple containing the username and password.
    """

    try:
        credentials = keyring.get_credential("TIDAL Access Token", None)
    except keyring.errors.KeyringLocked:
        return None, None, None, None
    info = ""
    if credentials:
        info = credentials.password
    if not info:
        return None, None, None, None
    info = info.split(':')
    access_key = info[0]
    refresh_key = info[1]
    expiry_time = info[2]
    token_type = info[3]
    return access_key, refresh_key, expiry_time, token_type


def pytest_collection_modifyitems(config, items):
    if config.getoption("--interactive"):
        return
    for item in items:
        if "interactive" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Skipping interactive tests"))


def pytest_addoption(parser):
    parser.addoption("--interactive", action="store_true", default=False, help="Run tests that require user input")
