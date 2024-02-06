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
"""pkce_login.py: A simple example script that describes how to use PKCE login and MPEG-DASH streams"""

import tidalapi
from tidalapi import Quality
from pathlib import Path

session_file1 = Path("tidal-session-pkce.json")

session = tidalapi.Session()
# Load session from file; create a new session if necessary
session.login_session_file(session_file1, do_pkce=True)

# Override the required playback quality, if necessary
# Note: Set the quality according to your subscription.
# Low: Quality.low_96k
# Normal: Quality.low_320k
# HiFi: Quality.high_lossless
# HiFi+ Quality.hi_res
# HiFi+ Quality.hi_res_lossless
session.audio_quality = Quality.hi_res_lossless.value
album_id = "77646169" #
album = session.album(album_id) # The Ballad of Darren
tracks = album.tracks()
# list album tracks
for track in tracks:
    print(track.name)
    # MPEG-DASH Stream is only supported when hi_res_lossless mode is used!
    stream = track.get_stream()
    hls = stream.get_stream_manifest().get_hls()
    with open("dash_{}_{}.m3u8".format(album_id, track.id), "w") as my_file:
        my_file.write(hls)