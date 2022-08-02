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
from .cover import verify_image_cover, verify_video_cover


def test_album(session):
    album = session.album(17927863)
    assert album.id == 17927863
    assert album.name == 'Some Things (Deluxe)'
    assert album.duration == 6712
    assert album.available
    assert album.num_tracks == 22
    assert album.num_videos == 0
    assert album.num_volumes == 2
    assert album.release_date == datetime.datetime(2011, 9, 22)
    assert album.copyright == 'Sinuz Recordings (a division of HITT bv)'
    assert album.version == 'Deluxe'
    assert album.cover == '30d83a8c-1db6-439d-84b4-dbfb6f03c44c'
    assert album.video_cover is None
    assert album.explicit is False
    assert album.universal_product_number == '3610151683488'
    assert 0 < album.popularity < 100
    assert album.artist.name == 'Lasgo'
    assert album.artists[0].name == 'Lasgo'

    with pytest.raises(AttributeError):
        session.album(17927863).video(1280)


def test_get_tracks(session):
    album = session.album(17927863)
    tracks = album.tracks()

    assert tracks[0].name == 'Intro'
    assert tracks[0].id == 17927864
    assert tracks[0].volume_num == 1
    assert tracks[0].track_num == 1

    assert tracks[-1].name == 'Pray'
    assert tracks[-1].id == 17927885
    assert tracks[-1].volume_num == 2
    assert tracks[-1].track_num == 8


def test_get_items(session):
    album = session.album(108043414)
    items = album.items()

    assert items[0].name == 'Pray You Catch Me'
    assert items[0].id == 108043415
    assert items[0].volume_num == 1
    assert items[0].track_num == 1

    assert items[-1].name == 'Lemonade Film'
    assert items[-1].id == 108043437
    assert items[-1].volume_num == 1
    assert items[-1].track_num == 15


def test_image_cover(session):
    verify_image_cover(session, session.album(108043414), [80, 160, 320, 640, 1280])


def test_video_cover(session):
    verify_video_cover(session.album(108043414), [80, 160, 320, 640, 1280])


def test_no_release_date(session):
    album = session.album(174114082)
    assert album.release_date is None
    assert album.tidal_release_date
    assert album.available_release_date == datetime.datetime(year=2021, month=3, day=9, tzinfo=tz.tzutc())


def test_no_cover(session):
    album = session.album(82804683)
    assert album.cover is None
    assert album.image(1280) == tidalapi.album.DEFAULT_ALBUM_IMAGE


def test_similar(session):
    album = session.album(108043414)
    for alb in album.similar():
        assert isinstance(alb.similar()[0], tidalapi.Album)


def test_review(session):
    album = session.album(199142349)
    review = album.review()
    assert "Kanye West" in review
