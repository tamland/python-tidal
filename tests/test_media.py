# -*- coding: utf-8 -*-
#
# Copyright (C) 2023- The Tidalapi Developers
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

from datetime import datetime

import pytest
import requests
from dateutil import tz

import tidalapi
from tidalapi.exceptions import MetadataNotAvailable

from .cover import verify_image_resolution, verify_video_resolution


def test_media(session):
    with pytest.raises(NotImplementedError):
        tidalapi.media.Media(session, 440930)


def test_track(session):
    track = session.track(125169484)

    assert track.name == "Alone, Pt. II"
    assert track.duration == 179
    assert track.replay_gain == -10.4
    assert track.peak == 0.988312
    assert track.available is True
    assert track.tidal_release_date == datetime(2019, 12, 27, 0, 0, tzinfo=tz.tzutc())
    assert track.track_num == 1
    assert track.volume_num == 1
    assert track.version is None
    assert (
        track.copyright
        == "(P) 2019 Kreatell Music under exclusive license to Sony Music Entertainment Sweden AB"
    )
    assert track.isrc == "NOG841907010"
    assert track.explicit is False
    assert track.audio_quality == tidalapi.Quality.hi_res
    assert track.album.name == "Alone, Pt. II"

    assert track.artist.name == "Alan Walker"
    artist_names = [artist.name for artist in track.artists]
    assert [artist in artist_names for artist in ["Alan Walker", "Ava Max"]]


def test_track_url(session):
    session.config = tidalapi.Config()
    track = session.track(142278122)
    assert "audio.tidal.com" in track.get_url()


def test_lyrics(session):
    track = session.track(56480040)
    lyrics = track.lyrics()
    assert "I think we're there" in lyrics.text
    assert "I think we're there" in lyrics.subtitles
    assert lyrics.right_to_left is False


def test_no_lyrics(session):
    track = session.track(17626400)
    # Tracks with no lyrics should trigger MetadataNotAvailable (response: 404)
    with pytest.raises(MetadataNotAvailable):
        track.lyrics()


def test_right_to_left(session):
    lyrics = session.track(95948697).lyrics()
    assert lyrics.right_to_left
    assert "أديني جيت" in lyrics.text


def test_track_with_album(session):
    track_id = 142278122
    track = session.track(track_id)
    print(track.album)
    assert track.album.duration is None
    track = session.track(track_id, True)
    assert track.album.duration == 221


def test_track_streaming(session):
    track = session.track(62392768)
    stream = track.get_stream()
    assert stream.audio_mode == tidalapi.media.AudioMode.stereo
    assert (
        stream.audio_quality == tidalapi.Quality.low_320k
    )  # i.e. the default quality for the current session


def test_video(session):
    video = session.video(125506698)

    assert video.id == 125506698
    assert video.name == "Alone, Pt. II"
    assert video.track_num == 0
    assert video.volume_num == 0
    assert video.release_date == datetime(2019, 12, 26, tzinfo=tz.tzutc())
    assert video.tidal_release_date == datetime(2019, 12, 27, 9, tzinfo=tz.tzutc())
    assert video.duration == 237
    assert video.video_quality == "MP4_1080P"
    assert video.available is True
    assert video.explicit is False
    assert video.type == "Music Video"
    assert video.album is None

    assert video.artist.name == "Alan Walker"
    artist_names = [artist.name for artist in video.artists]
    assert [artist in artist_names for artist in ["Alan Walker", "Ava Max"]]


def test_video_no_release_date(session):
    video = session.video(151050672)
    assert video.id == 151050672
    assert video.name == "Nachbarn"
    assert video.volume_num == 1
    assert video.track_num == 1
    assert video.release_date is None
    assert video.duration == 182
    assert video.available is True
    assert video.explicit is False
    assert video.type == "Music Video"
    assert video.album is None

    assert video.artist.name == "Harris & Ford"
    assert video.artists[0].name == "Harris & Ford"
    assert video.artists[1].name == "FiNCH"

    # Verify that we are clearing the release_date.
    videos = video.artists[1].get_videos()
    assert [None] == [
        video.release_date for video in videos if video.name == "Nachbarn"
    ]


def test_video_url(session):
    video = session.video(125506698)
    url = video.get_url()
    assert "m3u8" in url
    verify_video_resolution(url, 1920, 1080)


def test_live_video(session):
    live = session.video(179076073)
    assert live.id == 179076073
    assert live.name == "Justine Skye"
    assert live.track_num == 1
    assert live.volume_num == 1
    assert live.release_date == datetime(2021, 4, 1, tzinfo=tz.tzutc())
    assert live.tidal_release_date == datetime(2021, 4, 1, 18, tzinfo=tz.tzutc())
    assert live.duration == 204
    assert live.video_quality == "MP4_1080P"
    assert live.available is True
    assert live.explicit is False
    assert live.type == "Live"
    assert live.album is None

    assert live.artist.name == "SESSIONS"
    assert live.artists[0].name == "SESSIONS"


def test_video_image(session):
    video = session.video(125506698)

    resolutions = [(160, 107), (480, 320), (750, 500), (1080, 720)]
    for width, height in resolutions:
        verify_image_resolution(session, video.image(width, height), width, height)

    with pytest.raises(ValueError):
        video.image(81, 21)

    with pytest.raises(AssertionError):
        verify_image_resolution(session, video.image(1080, 720), 1270, 1270)


def test_full_name_track_1(session):
    track = session.track(149119714)
    assert track.name == "Fibonacci Progressions (Keemiyo Remix)"
    assert track.version is None
    assert track.full_name == "Fibonacci Progressions (Keemiyo Remix)"


def test_full_name_track_2(session):
    track = session.track(78495659)
    assert track.name == "Bullitt"
    assert track.version == "Bonus Track"
    assert track.full_name == "Bullitt (Bonus Track)"


def test_full_name_track_3(session):
    track = session.track(98849340)
    assert track.name == "Magical place (feat. IOVA)"
    assert track.version == "Dj Dark & MD Dj Remix"
    assert track.full_name == "Magical place (feat. IOVA) (Dj Dark & MD Dj Remix)"


def test_track_media_metadata_tags(session):
    track = session.track(182912246)
    assert track.name == "All You Ever Wanted"
    assert track.media_metadata_tags == ["LOSSLESS", "HIRES_LOSSLESS", "MQA"]


def test_get_track_radio_limit_default(session):
    track = session.track(182912246)
    similar_tracks = track.get_track_radio()
    assert len(similar_tracks) == 100


def test_get_track_radio_limit_25(session):
    track = session.track(182912246)
    similar_tracks = track.get_track_radio(limit=25)
    assert len(similar_tracks) == 25


def test_get_track_radio_limit_100(session):
    track = session.track(182912246)
    similar_tracks = track.get_track_radio(limit=100)
    assert len(similar_tracks) == 100
