# -*- coding: utf-8 -*-

# Copyright (C) 2023- The Tidalapi Developers
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
#
"""simple.py: A simple example script that describes how to get started using tidalapi"""

import tidalapi
from tidalapi import Quality
from pathlib import Path

oauth_file1 = Path("tidal-oauth-user.json")

session = tidalapi.Session()
# Will run until you visit the printed url and link your account
session.login_oauth_file(oauth_file1)
# Override the required playback quality, if necessary
# Note: Set the quality according to your subscription.
# Normal: Quality.low_320k
# HiFi: Quality.high_lossless
# HiFi+ Quality.hi_res_lossless
session.audio_quality = Quality.low_320k

album = session.album(66236918) # Electric For Life Episode 099
tracks = album.tracks()
print(album.name)
# list album tracks
for track in tracks:
    print(track.name)
    for artist in track.artists:
        print(' by: ', artist.name)