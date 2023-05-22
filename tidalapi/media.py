# -*- coding: utf-8 -*-

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

"""
A module containing information about various media types.

Classes: :class:`Media`, :class:`Track`, :class:`Video`
"""

import copy
import dateutil.parser
import tidalapi


class Media(object):
    """
    Base class for generic media, specifically :class:`Track` and :class:`Video`

    This class includes data used by both of the subclasses, and a function to parse both of them.

    The date_added attribute is only relevant for playlists.
    For the release date of the actual media, use the release date of the album.
    """
    id = None
    name = None
    duration = -1
    available = True
    tidal_release_date = None
    user_date_added = None
    track_num = -1
    volume_num = 1
    explicit = False
    popularity = -1
    artist = None
    #: For the artist credit page
    artist_roles = None
    artists = None
    album = None
    type = None

    def __init__(self, session, media_id=None):
        self.session = session
        self.requests = self.session.request
        self.album = session.album()
        self.id = media_id
        if media_id is not None:
            self._get(self.id)

    def _get(self, media_id):
        raise NotImplementedError("You are not supposed to use the media class directly.")

    def parse(self, json_obj):
        """
        Assigns all
        :param json_obj:
        :return:
        """
        artists = self.session.parse_artists(json_obj['artists'])

        # Sometimes the artist field is not filled, example: 62300893
        if 'artist' in json_obj:
            artist = self.session.parse_artist(json_obj['artist'])
        else:
            artist = artists[0]

        album = None
        if json_obj['album']:
            album = self.session.album().parse(json_obj['album'], artist, artists)

        self.id = json_obj['id']
        self.name = json_obj['title']
        self.duration = json_obj['duration']
        self.available = bool(json_obj['streamReady'])

        # Removed media does not have a release date.
        self.tidal_release_date = None
        release_date = json_obj.get('streamStartDate')
        self.tidal_release_date = dateutil.parser.isoparse(release_date) if release_date else None

        # When getting items from playlists they have a date added attribute, same with favorites.
        user_date_added = json_obj.get('dateAdded')
        self.user_date_added = dateutil.parser.isoparse(user_date_added) if user_date_added else None

        self.track_num = json_obj['trackNumber']
        self.volume_num = json_obj['volumeNumber']
        self.explicit = bool(json_obj['explicit'])
        self.popularity = json_obj['popularity']
        self.artist = artist
        self.artists = artists
        self.album = album
        self.type = json_obj.get('type')

        self.artist_roles = json_obj.get('artistRoles')

    def parse_media(self, json_obj):
        """
        Selects the media type when checking lists that can contain both.

        :param json_obj: The json containing the media
        :return: Returns a new Video or Track object.
        """
        if json_obj.get('type') is None or json_obj['type'] == 'Track':
            return Track(self.session).parse_track(json_obj)
        # There are other types like Event, Live, and Video witch match the video class
        return Video(self.session).parse_video(json_obj)


class Track(Media):
    """
    An object containing information about a track.
    """
    replay_gain = None
    peak = None
    isrc = None
    audio_quality = None
    version = None
    copyright = None

    def parse_track(self, json_obj):
        Media.parse(self, json_obj)
        self.replay_gain = json_obj['replayGain']
        # Tracks from the pages endpoints might not actually exist
        if 'peak' in json_obj and 'isrc' in json_obj:
            self.peak = json_obj['peak']
            self.isrc = json_obj['isrc']
            self.copyright = json_obj['copyright']
        self.audio_quality = tidalapi.Quality(json_obj['audioQuality'])
        self.version = json_obj['version']

        return copy.copy(self)

    def _get(self, media_id):
        """
        Returns information about a track, and also replaces the track used to call this function.

        :param media_id: TIDAL's identifier of the track
        :return: A :class:`Track` object containing all the information about the track
        """
        parse = self.parse_track
        return self.requests.map_request('tracks/%s' % media_id, parse=parse)

    def get_url(self):
        params = {
            'urlusagemode': 'STREAM',
            'audioquality' : self.session.config.quality,
            'assetpresentation': 'FULL',
        }
        request = self.requests.request('GET', 'tracks/%s/urlpostpaywall' % self.id, params)
        return request.json()['urls'][0]

    def lyrics(self):
        """
        Retrieves the lyrics for a song

        :return: A :class:`Lyrics` object containing the lyrics
        :raises: A :class:`requests.HTTPError` if there aren't any lyrics
        """
        return self.requests.map_request('tracks/%s/lyrics' % self.id, parse=Lyrics().parse)

    def get_track_radio(self):
        """
        Queries TIDAL for the track radio, which is a mix of tracks that are similar to this track.

        :return: A list of :class:`Tracks <tidalapi.media.Track>`
        """
        params = {'limit': 100}
        return self.requests.map_request('tracks/%s/radio' % self.id, params=params, parse=self.session.parse_track)

class Lyrics(object):
    track_id = -1
    provider = ""
    provider_track_id = -1
    provider_lyrics_id = -1
    text = ""
    #: Contains timestamps as well
    subtitles = ""
    right_to_left = False

    def parse(self, json_obj):
        self.track_id = json_obj['trackId']
        self.provider = json_obj['lyricsProvider']
        self.provider_track_id = json_obj['providerCommontrackId']
        self.provider_lyrics_id = json_obj['providerLyricsId']
        self.text = json_obj['lyrics']
        self.subtitles = json_obj['subtitles']
        self.right_to_left = bool(json_obj['isRightToLeft'])

        return copy.copy(self)


class Video(Media):
    """
    An object containing information about a video
    """
    release_date = None
    video_quality = None
    cover = None

    def parse_video(self, json_obj):
        Media.parse(self, json_obj)
        release_date = json_obj.get('releaseDate')
        self.release_date = dateutil.parser.isoparse(release_date) if release_date else None
        self.cover = json_obj['imageId']
        # Videos found in the /pages endpoints don't have quality
        self.video_quality = json_obj.get('quality')

        return copy.copy(self)

    def _get(self, media_id):
        """
        Returns information about the video, and replaces the object used to call this function.

        :param media_id: TIDAL's identifier of the video
        :return: A :class:`Video` object containing all the information about the video.
        """
        parse = self.parse_video
        return self.requests.map_request('videos/%s' % media_id, parse=parse)

    def get_url(self):
        params = {
            'urlusagemode': 'STREAM',
            'videoquality': self.session.config.video_quality,
            'assetpresentation': 'FULL'
        }
        request = self.requests.request('GET', 'videos/%s/urlpostpaywall' % self.id, params)
        return request.json()['urls'][0]

    def image(self, width=1080, height=720):
        if (width, height) not in [(160, 107), (480, 320), (750, 500), (1080, 720)]:
            raise ValueError("Invalid resolution {} x {}".format(width, height))

        return self.session.config.image_url % (self.cover.replace('-', '/'), width, height)
