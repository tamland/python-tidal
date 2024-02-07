# -*- coding: utf-8 -*-

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
"""A module containing information about various media types.

Classes: :class:`Media`, :class:`Track`, :class:`Video`
"""

from __future__ import annotations

import copy
from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Union, cast

import dateutil.parser

if TYPE_CHECKING:
    import tidalapi

import base64
import json
import re

import isodate
from mpegdash.parser import MPEGDASHParser

from tidalapi.exceptions import *
from tidalapi.types import JsonObj

# from mpd_parser.parser import Parser


class Quality(Enum):
    low_96k = "LOW"
    low_320k = "HIGH"
    high_lossless = "LOSSLESS"
    hi_res = "HI_RES"
    hi_res_lossless = "HI_RES_LOSSLESS"


class VideoQuality(Enum):
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"


class AudioMode(Enum):
    stereo = "STEREO"
    sony_360 = "SONY_360RA"
    dolby_atmos = "DOLBY_ATMOS"


# class MediaMetadataTags(Enum):
#    mqa = 'MQA'
#    hires_lossless = 'HIRES_LOSSLESS'
#    lossless = 'LOSSLESS'
#    sony_360 = 'SONY_360RA'
#    dolby_atmos = 'DOLBY_ATMOS'


class AudioExtensions(Enum):
    FLAC = ".flac"
    M4A = ".m4a"
    MP4 = ".mp4"


class VideoExtensions(Enum):
    TS = ".ts"


class ManifestMimeType(Enum):
    # EMU: str = "application/vnd.tidal.emu"
    # APPL: str = "application/vnd.apple.mpegurl"
    MPD: str = "application/dash+xml"
    BTS: str = "application/vnd.tidal.bts"
    VIDEO: str = "video/mp2t"


class Codec:
    MP3: str = "MP3"
    AAC: str = "AAC"
    M4A: str = "MP4A"
    FLAC: str = "FLAC"
    MQA: str = "MQA"
    Atmos: str = "EAC3"
    AC4: str = "AC4"
    SONY360RA: str = "MHA1"
    LowResCodecs: [str] = [MP3, AAC, M4A]
    PremiumCodecs: [str] = [MQA, Atmos, AC4]
    HQCodecs: [str] = PremiumCodecs + [FLAC]


class MimeType:
    audio_mpeg = "audio/mpeg"
    audio_mp3 = "audio/mp3"
    audio_m4a = "audio/m4a"
    audio_flac = "audio/flac"
    audio_xflac = "audio/x-flac"
    audio_eac3 = "audio/eac3"
    audio_ac4 = "audio/mp4"
    audio_m3u8 = "audio/mpegurl"
    video_mp4 = "video/mp4"
    video_m3u8 = "video/mpegurl"
    audio_map = {
        Codec.MP3: audio_mp3,
        Codec.AAC: audio_m4a,
        Codec.M4A: audio_m4a,
        Codec.FLAC: audio_xflac,
        Codec.MQA: audio_xflac,
        Codec.Atmos: audio_eac3,
        Codec.AC4: audio_ac4,
    }

    @staticmethod
    def from_audio_codec(codec):
        return MimeType.audio_map.get(codec, MimeType.audio_m4a)

    @staticmethod
    def is_FLAC(mime_type):
        return (
            True if mime_type in [MimeType.audio_flac, MimeType.audio_xflac] else False
        )


class Media:
    """Base class for generic media, specifically :class:`Track` and :class:`Video`

    This class includes data used by both of the subclasses, and a function to parse
    both of them.

    The date_added attribute is only relevant for playlists. For the release date of the
    actual media, use the release date of the album.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    duration: Optional[int] = -1
    available: bool = True
    tidal_release_date: Optional[datetime] = None
    user_date_added: Optional[datetime] = None
    track_num: int = -1
    volume_num: int = 1
    explicit: bool = False
    popularity: int = -1
    artist: Optional["tidalapi.artist.Artist"] = None
    #: For the artist credit page
    artist_roles = None
    artists: Optional[List["tidalapi.artist.Artist"]] = None
    album: Optional["tidalapi.album.Album"] = None
    type: Optional[str] = None

    def __init__(
        self, session: "tidalapi.session.Session", media_id: Optional[str] = None
    ):
        self.session = session
        self.requests = self.session.request
        self.album = session.album()
        self.id = media_id
        if self.id is not None:
            self._get(self.id)

    @abstractmethod
    def _get(self, media_id: str) -> Media:
        raise NotImplementedError(
            "You are not supposed to use the media class directly."
        )

    def parse(self, json_obj: JsonObj) -> None:
        """Assigns all :param json_obj:

        :return:
        """
        artists = self.session.parse_artists(json_obj["artists"])

        # Sometimes the artist field is not filled, example: 62300893
        if "artist" in json_obj:
            artist = self.session.parse_artist(json_obj["artist"])
        else:
            artist = artists[0]

        album = None
        if json_obj["album"]:
            album = self.session.album().parse(json_obj["album"], artist, artists)

        self.id = json_obj["id"]
        self.name = json_obj["title"]
        self.duration = json_obj["duration"]
        self.available = bool(json_obj["streamReady"])

        # Removed media does not have a release date.
        self.tidal_release_date = None
        release_date = json_obj.get("streamStartDate")
        self.tidal_release_date = (
            dateutil.parser.isoparse(release_date) if release_date else None
        )

        # When getting items from playlists they have a date added attribute, same with
        #  favorites.
        user_date_added = json_obj.get("dateAdded")
        self.user_date_added = (
            dateutil.parser.isoparse(user_date_added) if user_date_added else None
        )

        self.track_num = json_obj["trackNumber"]
        self.volume_num = json_obj["volumeNumber"]
        self.explicit = bool(json_obj["explicit"])
        self.popularity = json_obj["popularity"]
        self.artist = artist
        self.artists = artists
        self.album = album
        self.type = json_obj.get("type")

        self.artist_roles = json_obj.get("artistRoles")

    def parse_media(self, json_obj: JsonObj) -> Union["Track", "Video"]:
        """Selects the media type when checking lists that can contain both.

        :param json_obj: The json containing the media
        :return: Returns a new Video or Track object.
        """
        if json_obj.get("type") is None or json_obj["type"] == "Track":
            return Track(self.session).parse_track(json_obj)
        # There are other types like Event, Live, and Video witch match the video class
        return Video(self.session).parse_video(json_obj)


class Track(Media):
    """An object containing information about a track."""

    replay_gain = None
    peak = None
    isrc = None
    audio_quality: Optional[Quality] = None
    version = None
    full_name: Optional[str] = None
    copyright = None
    media_metadata_tags = None

    def parse_track(self, json_obj: JsonObj) -> Track:
        Media.parse(self, json_obj)
        self.replay_gain = json_obj["replayGain"]
        # Tracks from the pages endpoints might not actually exist
        if "peak" in json_obj and "isrc" in json_obj:
            self.peak = json_obj["peak"]
            self.isrc = json_obj["isrc"]
            self.copyright = json_obj["copyright"]
        self.audio_quality = Quality(json_obj["audioQuality"])
        self.version = json_obj["version"]
        self.media_metadata_tags = json_obj["mediaMetadata"]["tags"]

        if self.version is not None:
            self.full_name = f"{json_obj['title']} ({json_obj['version']})"
        else:
            self.full_name = json_obj["title"]

        return copy.copy(self)

    def _get(self, media_id: str) -> "Track":
        """Returns information about a track, and also replaces the track used to call
        this function.

        :param media_id: TIDAL's identifier of the track
        :return: A :class:`Track` object containing all the information about the track
        """
        parse = self.parse_track
        track = self.requests.map_request("tracks/%s" % media_id, parse=parse)
        assert not isinstance(track, list)
        return cast("Track", track)

    def get_url(self) -> str:
        if self.session.is_pkce:
            raise Exception(
                "Track URL not available with quality:'{}'".format(
                    self.session.config.quality
                )
            )
        params = {
            "urlusagemode": "STREAM",
            "audioquality": self.session.config.quality,
            "assetpresentation": "FULL",
        }
        json_obj = self.requests.map_request(
            "tracks/%s/urlpostpaywall" % self.id, params
        )
        if json_obj.get("status") and json_obj.get("status") == 404:
            raise AttributeError("URL not available for this track")
        else:
            return cast(str, json_obj["urls"][0])

    def lyrics(self) -> "Lyrics":
        """Retrieves the lyrics for a song.

        :return: A :class:`Lyrics` object containing the lyrics
        :raises: A :class:`requests.HTTPError` if there aren't any lyrics
        """

        json_obj = self.requests.map_request("tracks/%s/lyrics" % self.id)
        if json_obj.get("status") and json_obj.get("status") == 404:
            raise AttributeError("No lyrics exists for this track")
        else:
            lyrics = self.requests.map_json(json_obj, parse=Lyrics().parse)
            assert not isinstance(lyrics, list)
            return cast("Lyrics", lyrics)

    def get_track_radio(self, limit: int = 100) -> List["Track"]:
        """Queries TIDAL for the track radio, which is a mix of tracks that are similar
        to this track.

        :return: A list of :class:`Tracks <tidalapi.media.Track>`
        """
        params = {"limit": limit}
        tracks = self.requests.map_request(
            "tracks/%s/radio" % self.id, params=params, parse=self.session.parse_track
        )
        assert isinstance(tracks, list)
        return cast(List["Track"], tracks)

    def get_stream(self) -> "Stream":
        """Retrieves the track streaming object, allowing for audio transmission.

        :return: A :class:`Stream` object which holds audio file properties and
            parameters needed for streaming via `MPEG-DASH` protocol.
        """
        params = {
            "playbackmode": "STREAM",
            "audioquality": self.session.config.quality,
            "assetpresentation": "FULL",
        }
        stream = self.requests.map_request(
            "tracks/%s/playbackinfopostpaywall" % self.id, params, parse=Stream().parse
        )
        assert not isinstance(stream, list)
        return cast("Stream", stream)


class Stream:
    """An object that stores the audio file properties and parameters needed for
    streaming via `MPEG-DASH` protocol.

    The `manifest` attribute holds the MPD file content encoded in base64.
    """

    track_id: int = -1
    audio_mode: str = AudioMode.stereo.value  # STEREO, SONY_360RA, DOLBY_ATMOS
    audio_quality: str = Quality.low_96k.value  # LOW, HIGH, LOSSLESS, HI_RES
    manifest_mime_type: str = ""
    manifest_hash: str = ""
    manifest: str = ""

    def parse(self, json_obj: JsonObj) -> "Stream":
        self.track_id = json_obj["trackId"]
        self.audio_mode = json_obj["audioMode"]
        self.audio_quality = json_obj["audioQuality"]
        self.manifest_mime_type = json_obj["manifestMimeType"]
        self.manifest_hash = json_obj["manifestHash"]
        self.manifest = json_obj["manifest"]

        return copy.copy(self)

    def get_stream_manifest(self) -> "StreamManifest":
        return StreamManifest(self)


# @dataclass
# class StreamManifest:
#    codecs: str
#    mime_type: str
#    urls: [str]
#    file_extension: str
#    encryption_type: str | None = None
#    encryption_key: str | None = None


class StreamManifest:
    manifest: str = None
    manifest_mime_type: str = None
    manifest_parsed: str = None
    codecs: str = None  # MP3, AAC, FLAC, ALAC, MQA, EAC3, AC4, MHA1
    encryption_key = None
    encryption_type = None
    # bit_depth: int = 16
    sample_rate: int = 44100
    urls: [str] = []
    mime_type: MimeType = MimeType.audio_mpeg
    file_extension = None
    dash_info: DashInfo = None

    def __init__(self, stream: Stream):
        self.stream_manifest_parse(stream.manifest, stream.manifest_mime_type)

    def stream_manifest_parse(self, manifest: str, mime_type: str):
        self.manifest = manifest
        self.manifest_mime_type = mime_type
        if self.manifest_mime_type == ManifestMimeType.MPD.value:
            # Stream Manifest is base64 encoded.
            self.dash_info = DashInfo.from_base64(manifest)
            self.urls = self.dash_info.urls
            self.codecs = self.dash_info.codecs
            self.mime_type = self.dash_info.mimeType
            # self.bit_depth
            self.sample_rate = self.dash_info.audioSamplingRate
            # TODO: Handle encryption key.
            self.encryption_type = "NONE"
            self.encryption_key = None
        elif self.manifest_mime_type == ManifestMimeType.BTS.value:
            # Stream Manifest is base64 encoded.
            self.manifest_parsed: str = base64.b64decode(manifest).decode("utf-8")
            # JSON string to object.
            stream_manifest = json.loads(self.manifest_parsed)
            # TODO: Handle more than one download URL
            self.urls = stream_manifest["urls"]
            self.codecs = stream_manifest["codecs"].upper().split(".")[0]
            self.mime_type = stream_manifest["mimeType"]
            # self.bit_depth
            # self.sample_rate
            self.encryption_type = stream_manifest["encryptionType"]
            self.encryption_key = (
                stream_manifest["encryptionKey"] if self.is_encrypted else None
            )
        else:
            raise UnknownManifestFormat

        self.file_extension = self.get_file_extension(self.urls[0])

    def get_manifest_data(self):
        try:
            return base64.b64decode(self.manifest).decode("utf-8")
        except:
            raise StreamManifestDecodeError
        return ""

    def get_urls(self):
        return self.urls

    def get_hls(self):
        if self.is_MPD:
            return self.dash_info.get_hls()
        else:
            raise MPDUnavailableError("HLS stream requires MPD MetaData")

    def get_codecs(self):
        return self.dash_info.codecs

    def get_sampling_rate(self):
        return self.dash_info.audioSamplingRate

    @staticmethod
    def get_mimetype(stream_codec, stream_url: Optional[str] = None):
        if stream_codec:
            return MimeType.from_audio_codec(stream_codec)
        if not stream_url:
            return MimeType.audio_m4a
        else:
            if AudioExtensions.FLAC.value in stream_url:
                return MimeType.audio_xflac
            elif AudioExtensions.MP4.value in stream_url:
                return MimeType.audio_m4a

    @staticmethod
    def get_file_extension(stream_url: str, stream_codec: Optional[str] = None) -> str:
        if AudioExtensions.FLAC.value in stream_url:
            result: str = AudioExtensions.FLAC.value
        elif AudioExtensions.MP4.value in stream_url:
            # TODO: Need to investigate, what the correct extension is.
            # if "ac4" in stream_codec or "mha1" in stream_codec:
            #     result = ".mp4"
            # elif "flac" in stream_codec:
            #     result = ".flac"
            # else:
            #     result = ".m4a"
            result: str = AudioExtensions.MP4.value
        elif VideoExtensions.TS.value in stream_url:
            result: str = VideoExtensions.TS.value
        else:
            result: str = AudioExtensions.M4A.value

        return result

    @property
    def is_encrypted(self):
        return True if self.encryption_key else False

    @property
    def is_MPD(self):
        return True if ManifestMimeType.MPD.value in self.manifest_mime_type else False


class DashInfo:
    @staticmethod
    def from_stream(stream):
        try:
            if stream.is_MPD and not stream.is_encrypted:
                return DashInfo(stream.get_manifest_data())
        except:
            return None

    @staticmethod
    def from_base64(mpd_manifest_base64):
        try:
            return DashInfo(base64.b64decode(mpd_manifest_base64).decode("utf-8"))
        except:
            return None

    def __init__(self, mpd_xml):
        self.manifest = mpd_xml

        mpd = MPEGDASHParser.parse(mpd_xml.split("?>")[1])
        self.duration = isodate.parse_duration(mpd.media_presentation_duration)
        self.contentType = mpd.periods[0].adaptation_sets[0].content_type
        self.mimeType = mpd.periods[0].adaptation_sets[0].mime_type
        self.codecs = mpd.periods[0].adaptation_sets[0].representations[0].codecs
        self.firstUrl = (
            mpd.periods[0]
            .adaptation_sets[0]
            .representations[0]
            .segment_templates[0]
            .initialization
        )
        self.mediaUrl = (
            mpd.periods[0]
            .adaptation_sets[0]
            .representations[0]
            .segment_templates[0]
            .media
        )
        # self.startNumber = mpd.periods[0].adaptation_sets[0].representations[0].segment_templates[0].start_number
        self.timescale = (
            mpd.periods[0]
            .adaptation_sets[0]
            .representations[0]
            .segment_templates[0]
            .timescale
        )
        self.audioSamplingRate = int(
            mpd.periods[0].adaptation_sets[0].representations[0].audio_sampling_rate
        )
        self.chunksize = (
            mpd.periods[0]
            .adaptation_sets[0]
            .representations[0]
            .segment_templates[0]
            .segment_timelines[0]
            .Ss[0]
            .d
        )
        # self.chunkcount = mpd.periods[0].adaptation_sets[0].representations[0].segment_templates[0].segment_timelines[0].Ss[0].r + 1
        self.lastchunksize = (
            mpd.periods[0]
            .adaptation_sets[0]
            .representations[0]
            .segment_templates[0]
            .segment_timelines[0]
            .Ss[1]
            .d
        )

        self.urls = self.get_urls(mpd)

    @staticmethod
    def get_urls(mpd):
        # min segments count; i.e. .initialization + the very first of .media;
        # See https://developers.broadpeak.io/docs/foundations-dash
        segments_count = 1 + 1

        for s in (
            mpd.periods[0]
            .adaptation_sets[0]
            .representations[0]
            .segment_templates[0]
            .segment_timelines[0]
            .Ss
        ):
            segments_count += s.r if s.r else 1

        # Populate segment urls.
        segment_template = (
            mpd.periods[0]
            .adaptation_sets[0]
            .representations[0]
            .segment_templates[0]
            .media
        )
        stream_urls: list[str] = []

        for index in range(segments_count):
            stream_urls.append(segment_template.replace("$Number$", str(index)))

        return stream_urls

    def get_hls(self):
        hls = "#EXTM3U\n"
        hls += "#EXT-X-TARGETDURATION:%s\n" % int(self.duration.seconds)
        hls += "#EXT-X-VERSION:3\n"
        items = self.urls
        chunk_duration = "#EXTINF:%0.3f,\n" % (
            float(self.chunksize) / float(self.timescale)
        )
        hls += "\n".join(chunk_duration + item for item in items[0:-1])
        chunk_duration = "#EXTINF:%0.3f,\n" % (
            float(self.lastchunksize) / float(self.timescale)
        )
        hls += "\n" + chunk_duration + items[-1] + "\n"
        hls += "#EXT-X-ENDLIST\n"
        return hls


class Lyrics:
    track_id: int = -1
    provider: str = ""
    provider_track_id: int = -1
    provider_lyrics_id: int = -1
    text: str = ""
    #: Contains timestamps as well
    subtitles: str = ""
    right_to_left: bool = False

    def parse(self, json_obj: JsonObj) -> "Lyrics":
        self.track_id = json_obj["trackId"]
        self.provider = json_obj["lyricsProvider"]
        self.provider_track_id = json_obj["providerCommontrackId"]
        self.provider_lyrics_id = json_obj["providerLyricsId"]
        self.text = json_obj["lyrics"]
        self.subtitles = json_obj["subtitles"]
        self.right_to_left = bool(json_obj["isRightToLeft"])

        return copy.copy(self)


class Video(Media):
    """An object containing information about a video."""

    release_date: Optional[datetime] = None
    video_quality: Optional[str] = None
    cover: Optional[str] = None

    def parse_video(self, json_obj: JsonObj) -> Video:
        Media.parse(self, json_obj)
        release_date = json_obj.get("releaseDate")
        self.release_date = (
            dateutil.parser.isoparse(release_date) if release_date else None
        )
        self.cover = json_obj["imageId"]
        # Videos found in the /pages endpoints don't have quality
        self.video_quality = json_obj.get("quality")

        return copy.copy(self)

    def _get(self, media_id: str) -> Video:
        """Returns information about the video, and replaces the object used to call
        this function.

        :param media_id: TIDAL's identifier of the video
        :return: A :class:`Video` object containing all the information about the video.
        """
        parse = self.parse_video
        video = self.requests.map_request("videos/%s" % media_id, parse=parse)
        assert not isinstance(video, list)
        return cast("Video", video)

    def get_url(self) -> str:
        params = {
            "urlusagemode": "STREAM",
            "videoquality": self.session.config.video_quality,
            "assetpresentation": "FULL",
        }
        request = self.requests.request(
            "GET", "videos/%s/urlpostpaywall" % self.id, params
        )
        return cast(str, request.json()["urls"][0])

    def image(self, width: int = 1080, height: int = 720) -> str:
        if (width, height) not in [(160, 107), (480, 320), (750, 500), (1080, 720)]:
            raise ValueError("Invalid resolution {} x {}".format(width, height))
        if not self.cover:
            raise AttributeError("No cover image")
        return self.session.config.image_url % (
            self.cover.replace("-", "/"),
            width,
            height,
        )
