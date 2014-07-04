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
import wimpy

logging.basicConfig(level=logging.DEBUG)

def test_artist():
    session = wimpy.Session()
    albums = session.get_albums(18888)
    assert len(albums) > 0

def test_album():
    session = wimpy.Session()
    tracks = session.get_album(16909093)
    assert len(tracks) > 0

def test_search():
    session = wimpy.Session(session_id='asd')
    artists = session.search('artists', 'mala')
    assert artists[0].name == "Mala"
