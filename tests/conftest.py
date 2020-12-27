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

import logging
import os
import keyring
import pytest
import tidalapi


@pytest.fixture(scope='session')
def session():
    logging.basicConfig(level=logging.DEBUG)
    username, password = get_credentials()
    config = tidalapi.Config(quality=tidalapi.Quality.lossless)
    tidal_session = tidalapi.Session(config)
    tidal_session.login(username, password)
    return tidal_session


def get_credentials():
    """
    Attempt to get the password and username from env variables or the keyring.

    :return: Returns a tuple containing the username and password.
    """
    username = os.getenv("TIDAL_USERNAME")
    password = os.getenv("TIDAL_PASSWORD")

    if not username and not password:
        credentials = keyring.get_credential('TIDAL', None)
        username = credentials.username
        password = credentials.password

    return username, password
