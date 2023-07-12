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

import datetime

import pytest
from dateutil import tz

import tidalapi

from .cover import verify_image_cover, verify_image_resolution


def test_playlist(session):
    playlist = session.playlist("7eafb342-141a-4092-91eb-da0012da3a19")

    assert playlist.id == "7eafb342-141a-4092-91eb-da0012da3a19"
    assert playlist.name == "JAY-Z's Year End Picks 2019"
    assert playlist.num_tracks == 40
    assert (
        playlist.description
        == "JAY-Z shares his favorite Hip-Hop and R&B songs from the year."
        " (Photo: Ravie B.)"
    )
    assert playlist.duration == 8008
    assert playlist.last_updated == datetime.datetime(
        2021, 12, 9, 17, 13, 40, 932000, tzinfo=tz.tzutc()
    )

    assert playlist.created == datetime.datetime(
        2019, 12, 19, 17, 15, 5, 500000, tzinfo=tz.tzutc()
    )
    assert playlist.type == "ARTIST"
    assert playlist.public is True
    assert playlist.popularity == 0
    assert len(playlist.promoted_artists) == 4

    creator = playlist.creator
    assert creator.id == 7804
    assert creator.name == "JAY Z"
    assert isinstance(creator, tidalapi.Artist)


def test_updated_playlist(session):
    playlist = session.playlist("944dd087-f65c-4954-a9a3-042a574e86e3")
    assert playlist.id == "944dd087-f65c-4954-a9a3-042a574e86e3"
    assert playlist.name == "lofi"
    assert playlist.num_tracks >= 5288
    assert playlist.description == ""
    assert playlist.duration >= 693350
    assert playlist.last_updated >= datetime.datetime(2020, 5, 14, tzinfo=tz.tzutc())
    assert playlist.created == datetime.datetime(
        2020, 4, 15, 15, 15, 37, 282000, tzinfo=tz.tzutc()
    )
    assert playlist.type == "USER"
    assert playlist.public is False
    assert playlist.popularity == 0
    assert playlist.promoted_artists is None

    creator = playlist.creator
    assert creator.id == 169584258
    assert creator.name == "user"


def test_video_playlist(session):
    playlist = session.playlist("aa3611ff-5b25-4bbe-8ce4-36c678c3438f")
    assert playlist.id == "aa3611ff-5b25-4bbe-8ce4-36c678c3438f"
    assert playlist.name == "TIDAL X Sundance"
    assert playlist.num_tracks == 0
    assert playlist.num_videos == 12
    assert (
        playlist.description == "In partnership with Vulture, "
        "TIDAL talks to actors and musicians at the 2017 Sundance Film Festival "
        "about the meeting of music and film. #tidalxvulture (Photo: TIDAL) "
    )
    assert playlist.duration == 1996
    assert playlist.last_updated == datetime.datetime(
        2020, 3, 25, 8, 5, 33, 115000, tzinfo=tz.tzutc()
    )
    assert playlist.created == datetime.datetime(
        2017, 1, 23, 18, 34, 56, 930000, tzinfo=tz.tzutc()
    )
    assert playlist.type == "EDITORIAL"
    assert playlist.public is True
    assert playlist.promoted_artists[0].name == "Sundance Film Festival"

    creator = playlist.creator
    assert creator.id == 0
    assert creator.name == "TIDAL"


def test_get_tracks(session):
    playlist = session.playlist("944dd087-f65c-4954-a9a3-042a574e86e3")
    remaining = 0

    items = []
    while remaining < playlist.num_tracks:
        new_items = playlist.tracks(limit=1000, offset=remaining)
        remaining += len(new_items)
        items.extend(new_items)

    assert len(items) >= 5288
    assert items[0].id == 199477058
    assert items[5287].id == 209284860


def test_get_videos(session):
    playlist = session.playlist("aa3611ff-5b25-4bbe-8ce4-36c678c3438f")
    items = playlist.items()
    assert all([isinstance(item, tidalapi.Video) for item in items])
    assert items[0].name == "Day 1: Part 1"
    assert items[-1].name == "Sundance 2017 Recap"


def test_image(session):
    playlist = session.playlist("33136f5a-d93a-4469-9353-8365897aaf94")
    verify_image_cover(session, playlist, [160, 320, 480, 640, 750, 1080])


def test_wide_image(session):
    playlist = session.playlist("7eafb342-141a-4092-91eb-da0012da3a19")
    resolutions = [(160, 107), (480, 320), (750, 500), (1080, 720)]

    for width, height in resolutions:
        verify_image_resolution(
            session, playlist.wide_image(width, height), width, height
        )

    with pytest.raises(ValueError):
        playlist.wide_image(81, 21)

    with pytest.raises(AssertionError):
        verify_image_resolution(session, playlist.wide_image(1080, 720), 1270, 1270)
