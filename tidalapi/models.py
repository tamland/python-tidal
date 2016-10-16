# -*- coding: utf-8 -*-
#
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

from __future__ import unicode_literals

import re
import datetime

IMG_URL = 'http://resources.tidal.com/images/{picture}/{size}.jpg'
ARTIST_IMAGE_URL = 'http://images.tidalhifi.com/im/im?w={width}&h={height}&artistid={artistid}'
VIDEO_IMAGE_URL = 'http://images.tidalhifi.com/im/im?w={width}&h={height}&img={imagepath}'

DEFAULT_ARTIST_IMG = '1e01cdb6-f15d-4d8b-8440-a047976c1cac'
DEFAULT_ALBUM_IMG = '0dfd3368-3aa1-49a3-935f-10ffb39803c0'
DEFAULT_PLAYLIST_IMG = '443331e2-0421-490c-8918-5a4867949589' 
DEFAULT_VIDEO_IMB = 'fa6f0650-76ac-41d1-a4a3-7fe4c89fca90'

CATEGORY_IMAGE_SIZES = {'genres': '460x306', 'moods': '342x342'}

RE_ISO8601 = re.compile(r'^(?P<full>((?P<year>\d{4})([/-]?(?P<month>(0[1-9])|(1[012]))([/-]?(?P<day>(0[1-9])|([12]\d)|(3[01])))?)?(?:[\sT](?P<hour>([01][0-9])|(?:2[0123]))(\:?(?P<minute>[0-5][0-9])(\:?(?P<second>[0-5][0-9])(?P<ms>([\,\.]\d{1,10})?))?)?(?:Z|([\-+](?:([01][0-9])|(?:2[0123]))(\:?(?:[0-5][0-9]))?))?)?))$')


class Quality(object):
    lossless = 'LOSSLESS'
    high = 'HIGH'
    low = 'LOW'
    trial = 'TRIAL' # 30 Seconds MP3 Stream


class SubscriptionType(object):
    premium = 'PREMIUM'
    hifi = 'HIFI'
    free = 'FREE'


class Model(object):
    id = None
    name = 'Unknown'

    def parse_date(self, datestring):
        try:
            d = RE_ISO8601.match(datestring).groupdict()
            if d['hour'] and d['minute'] and d['second']:
                return datetime.datetime(year=int(d['year']), month=int(d['month']), day=int(d['day']), hour=int(d['hour']), minute=int(d['minute']), second=int(d['second']))
            else:
                return datetime.datetime(year=int(d['year']), month=int(d['month']), day=int(d['day']))
        except:
            pass
        return None


class BrowsableMedia(Model):

    # Internal Properties
    _isFavorite = False
    _itemPosition = -1
    _offset = 0
    _totalNumberOfItems = 0

    @property
    def image(self):
        return None

    @property
    def fanart(self):
        return None


class Album(BrowsableMedia):
    title = 'Unknown'
    artist = None
    artists = []
    duration = -1
    numberOfTracks = 1
    numberOfVolumes = 1
    allowStreaming = True
    streamReady = True
    premiumStreamingOnly = False
    streamStartDate = None
    releaseDate = None
    cover = None
    type = 'ALBUM'
    explicit = False
    version = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Album, self).__init__()
        if self.releaseDate:
            self.releaseDate = self.parse_date(self.releaseDate)
        if self.streamStartDate:
            self.streamStartDate = self.parse_date(self.streamStartDate)
        self.num_tracks = self.numberOfTracks # For Backward Compatibility
        self.release_date = self.releaseDate  # For Backward Compatibility
        self.name = self.title                # For Backward Compatibility

    @property
    def year(self):
        if self.releaseDate:
            return self.releaseDate.year
        if self.streamStartDate:
            return self.streamStartDate.year
        return None

    @property
    def image(self):
        if self.cover:
            return IMG_URL.format(picture=self.cover.replace('-', '/'), size='640x640')
        return IMG_URL.format(picture=DEFAULT_ALBUM_IMG.replace('-', '/'), size='640x640')

    @property
    def fanart(self):
        if self.artist and isinstance(self.artist, Artist):
            return self.artist.fanart
        if self.cover:
            return IMG_URL.format(picture=self.cover.replace('-', '/'), size='1280x1280')
        return None


class Artist(BrowsableMedia):
    picture = None
    url = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Artist, self).__init__()

    @property
    def image(self):
        if self.picture:
            return IMG_URL.format(picture=self.picture.replace('-', '/'), size='320x320')
        return IMG_URL.format(picture=DEFAULT_ARTIST_IMG.replace('-', '/'), size='320x320')

    @property
    def fanart(self):
        if self.picture:
            return IMG_URL.format(picture=self.picture.replace('-', '/'), size='1080x720')
        return ARTIST_IMAGE_URL.format(width=1080, height=720, artistid=self.id)


class Playlist(BrowsableMedia):
    description = None
    creator = None
    type = None
    uuid = None
    title = 'Unknown'
    created = None
    creationDate = None
    publicPlaylist = None
    lastUpdated = None
    numberOfTracks = 0
    numberOfVideos = 0
    duration = -1

    # Internal Properties
    _image = None  # For Backward Compatibility because "image" is a property method
    _etag = None   # ETag from HTTP Response Header for Playlist Operations

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Playlist, self).__init__()
        self.id = self.uuid
        self.is_public = self.publicPlaylist # For Backward Compatibility
        self.last_updated = self.lastUpdated # For Backward Compatibility
        self.num_tracks = self.numberOfItems # For Backward Compatibility
        self.name = self.title               # For Backward Compatibility
        self._image = kwargs.get('image', None) # Because "image" is a property method
        if self.created:
            # New Property for Backward Compatibility
            self.creationDate = self.parse_date(self.created)
        if self.lastUpdated:
            self.lastUpdated = self.parse_date(self.lastUpdated)
        else:
            self.lastUpdated = self.creationDate

    @property
    def numberOfItems(self):
        return self.numberOfTracks + self.numberOfVideos

    @property
    def year(self):
        if self.lastUpdated:
            return self.lastUpdated.year
        elif self.creationDate:
            return self.creationDate.year
        return datetime.datetime.now().year

    @property
    def image(self):
        if self._image:
            return IMG_URL.format(picture=self._image.replace('-', '/'), size='320x214')
        return IMG_URL.format(picture=DEFAULT_PLAYLIST_IMG.replace('-', '/'), size='320x214')

    @property
    def fanart(self):
        if self._image:
            return IMG_URL.format(picture=self._image.replace('-', '/'), size='1080x720')
        return None


class PlayableMedia(BrowsableMedia):
    # Common Properties for Tacks and Videos
    title = 'Unknown'
    artist = None
    artists = []
    version = None
    explicit = False
    duration = 30
    allowStreaming = True
    streamReady = True
    streamStartDate = None

    # Internal Properties
    _playlist_id = None        # ID of the Playlist
    _playlist_pos = -1         # Item position in playlist
    _etag = None               # ETag for User Playlists
    _playlist_name = None      # Name of Playlist
    _playlist_type = ''        # Playlist Type

    def __init__(self):
        super(PlayableMedia, self).__init__()
        if self.streamStartDate:
            self.streamStartDate = self.parse_date(self.streamStartDate)
        self.name = self.title  # For Backward Compatibility

    @property
    def year(self):
        if self.streamStartDate:
            return self.streamStartDate.year
        return datetime.datetime.now().year

    @property
    def available(self):
        return self.streamReady and self.allowStreaming


class Track(PlayableMedia):
    trackNumber = 1
    volumeNumber = 1
    album = None
    popularity = 0
    isrc = None
    premiumStreamingOnly = False
    replayGain = 0.0
    peak = 1.0

    # Internal Properties
    _ftArtists = []  # All artists except main (Filled by parser)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Track, self).__init__()
        self.track_num = self.trackNumber # For Backward Compatibility
        self.disc_num =self.volumeNumber  # For Backward Compatibility
        self.popularity = int("0%s" % self.popularity)

    @property
    def year(self):
        if self.album and isinstance(self.album, Album) and getattr(self.album, 'year', None):
            return self.album.year
        return super(Track, self).year

    @property
    def image(self):
        if self.album and isinstance(self.album, Album):
            return self.album.image
        return IMG_URL.format(picture=DEFAULT_ALBUM_IMG.cover.replace('-', '/'), size='640x640')

    @property
    def fanart(self):
        if self.artist and isinstance(self.artist, Artist):
            return self.artist.fanart
        return None


class Video(PlayableMedia):
    releaseDate = None
    quality = None
    imageId = None
    imagePath = None

    # Internal Properties
    _ftArtists = []  # All artists except main (Filled by parser)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Video, self).__init__()
        if self.releaseDate:
            self.releaseDate = self.parse_date(self.releaseDate)

    @property
    def year(self):
        if self.releaseDate:
            return self.releaseDate.year
        return super(Video, self).year

    @property
    def image(self):
        if self.imageId:
            return IMG_URL.format(picture=self.imageId.replace('-', '/'), size='320x214')
        elif self.imagePath:
            return VIDEO_IMAGE_URL.format(width=320, height=214, imagepath=self.imagePath)
        return IMG_URL.format(picture=DEFAULT_VIDEO_IMB.replace('-', '/'), size='320x214')

    @property
    def fanart(self):
        if self.artist and isinstance(self.artist, Artist):
            return self.artist.fanart
        elif self.imagePath:
            return VIDEO_IMAGE_URL.format(width=320, height=214, imagepath=self.imagePath)
        return None

    def getFtArtistsText(self):
        text = ''
        for item in self._ftArtists:
            if len(text) > 0:
                text = text + ', '
            text = text + item.name
        if len(text) > 0:
            text = 'ft. by ' + text
        return text


class Promotion(BrowsableMedia):
    header = None
    subHeader = None
    shortHeader = None
    shortSubHeader = None
    standaloneHeader = None
    group = None        # NEWS|DISCOVERY|RISING
    created = None
    text = None
    imageId = None
    imageURL = None
    type = None         # PLAYLIST|ALBUM|VIDEO|EXTURL
    artifactId = None
    duration= 0

    # Internal Properties
    _artist = None       # filled by parser

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Promotion, self).__init__()
        if self.created:
            self.created = self.parse_date(self.created)
        self.id = '%s' % self.artifactId
        self.id = self.id.strip()
        self.name = self.shortHeader

    @property
    def image(self):
        if self.imageId:
            return IMG_URL.format(picture=self.imageId.replace('-', '/'), size='550x400')
        return self.imageURL

    @property
    def fanart(self):
        if self.imageId:
            return IMG_URL.format(picture=self.imageId.replace('-', '/'), size='550x400')
        return self.imageURL


class Category(BrowsableMedia):
    path = None
    hasAlbums = False
    hasArtists = False
    hasPlaylists = False
    hasTracks = False
    hasVideos = False

    # Internal Properties
    _image = None   # "image" is also a property
    _group = ''

    @staticmethod
    def groups():
        return ['featured', 'rising', 'discovery', 'genres', 'moods', 'movies', 'shows']

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Category, self).__init__()
        self.id = self.path
        self._image = kwargs.get('image', None) # Because "image" is a property

    @property
    def image(self):
        if self._image:
            return IMG_URL.format(picture=self._image.replace('-', '/'), size=CATEGORY_IMAGE_SIZES.get(self._group, '512x512'))
        return None

    @property
    def fanart(self):
        if self._image:
            return IMG_URL.format(picture=self._image.replace('-', '/'), size=CATEGORY_IMAGE_SIZES.get(self._group, '512x512'))
        return None

    @property
    def content_types(self):
        types = []
        if self.hasArtists:   types.append('artists')
        if self.hasAlbums:    types.append('albums')
        if self.hasPlaylists: types.append('playlists')
        if self.hasTracks:    types.append('tracks')
        if self.hasVideos:    types.append('videos')
        return types


class Role(object):
    main = 'MAIN'
    featured = 'FEATURED'


class SearchResult(Model):
    ''' List of Search Result Items '''
    artists = []
    albums = []
    tracks = []
    playlists = []
    videos = []

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(SearchResult, self).__init__()


class UserInfo(Model):
    username = ''
    firstName = ''
    lastName = ''
    email = ''
    created = None
    picture = None
    newsletter = False
    gender = 'm'
    dateOfBirth = None
    facebookUid = '0'
    subscription = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(UserInfo, self).__init__()
        if self.created:
            self.created = self.parse_date(self.created)
        if self.dateOfBirth:
            self.dateOfBirth = self.parse_date(self.dateOfBirth)
        self.facebookUid = '%s' % self.facebookUid
        self.name = self.username


class Subscription(Model):
    subscription = {'type': SubscriptionType.hifi}
    status = 'ACTIVE'
    validUntil = None
    highestSoundQuality = None
    premiumAccess = True
    canGetTrial = False
    paymentType = ''

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Subscription, self).__init__()
        if not self.highestSoundQuality:
            # Determine highest sound quality with subscription type 
            self.highestSoundQuality = {SubscriptionType.hifi: Quality.lossless, 
                                        SubscriptionType.premium: Quality.high,
                                        SubscriptionType.free: Quality.low}.get(self.type, Quality.high)
        self.validUntil = self.parse_date(self.validUntil if self.validUntil else '2099-12-31')

    @property
    def type(self):
        try:
            return self.subscription.get('type', SubscriptionType.hifi)
        except:
            return SubscriptionType.hifi

    @type.setter
    def type(self, value):
        self.subscription = {'type': value}

    @property
    def isValis(self):
        return self.validUntil >= datetime.datetime.now()
