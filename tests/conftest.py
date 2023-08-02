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
from abc import ABC
from contextlib import suppress
from json import dumps, loads
from os import getenv
from pathlib import Path
from typing import List, Optional

import keyring
import keyring.backends
import keyring.errors
import pytest

import tidalapi


@pytest.fixture(scope="session")
def session(request):
    logging.basicConfig(level=logging.DEBUG)
    return login(request)


class Credentials(ABC):
    def load(self, key: str) -> Optional[dict]:
        """Load secret."""

    def save(self, key: str, val: dict) -> None:
        """Save secret."""


class EnvCredentials(Credentials):
    def load(self, key: str) -> Optional[dict]:
        credentials = {
            "token_type": getenv("TIDAL_TOKEN_TYPE", "Bearer"),
            "access_token": getenv("TIDAL_ACCESS_TOKEN"),
            "refresh_token": getenv("TIDAL_REFRESH_TOKEN"),
        }
        return (
            credentials
            if credentials["access_token"] and credentials["refresh_token"]
            else None
        )

    def save(self, key: str, val: dict) -> None:
        print("Credentials are:")
        print(val)


class KeyringCredentials(Credentials):
    def load(self, key: str) -> Optional[dict]:
        with suppress(Exception):
            credentials = keyring.get_password(key, key)
            return loads(credentials)
        return None

    def save(self, key: str, val: dict) -> None:
        keyring.set_password(key, key, dumps(val))


class CachedCredentials(Credentials):
    def __init__(self):
        base_dir = Path("~/.local/cache").expanduser()
        if not base_dir.exists():
            raise FileNotFoundError(f"No cache directory {base_dir}")
        self.cache_dir = base_dir / "python-tidal"
        self.cache_dir.mkdir(exist_ok=True)

    def load(self, key: str) -> Optional[dict]:
        cachef = self.cache_dir / f"{key}.json"
        try:
            return loads(cachef.read_text())
        except Exception:
            return None

    def save(self, key: str, val: dict) -> None:
        cachef = self.cache_dir / f"{key}.json"
        cachef.write_text(dumps(val))


KEY = "python-tidal"


def get_credential_store() -> tuple[List[Credentials], Optional[dict]]:
    stores = []
    for store in (EnvCredentials, CachedCredentials, KeyringCredentials):
        with suppress(Exception):
            stores.append(store())
    for store in stores:
        data = store.load(KEY)
        if data:
            return [store], data
    stores = [s for s in stores if not isinstance(s, EnvCredentials)]
    return stores, None


def login(request):
    stores, credentials = get_credential_store()
    config = tidalapi.Config(quality=tidalapi.Quality.master)
    tidal_session = tidalapi.Session(config)
    if credentials and tidal_session.load_oauth_session(**credentials):
        return tidal_session
    else:
        credentials = _oauth_login(request, tidal_session)

    if stores:
        for store in stores:
            with suppress(Exception):
                store.save(
                    KEY,
                    {
                        "token_type": tidal_session.token_type,
                        "access_token": tidal_session.access_token,
                        "refresh_token": tidal_session.refresh_token,
                    },
                )
                break
    return tidal_session


def _oauth_login(request, tidal_session):
    login, future = tidal_session.login_oauth()
    # https://github.com/pytest-dev/pytest/issues/2704
    capmanager = request.config.pluginmanager.getplugin("capturemanager")
    with capmanager.global_and_fixture_disabled():
        print(
            "Visit",
            "https://" + login.verification_uri_complete,
            "to log in, the link expires in",
            login.expires_in,
            "seconds",
        )
    future.result()


def pytest_collection_modifyitems(config, items):
    if config.getoption("--interactive"):
        return
    for item in items:
        if "interactive" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Skipping interactive tests"))


def pytest_addoption(parser):
    parser.addoption(
        "--interactive",
        action="store_true",
        default=False,
        help="Run tests that require user input",
    )
