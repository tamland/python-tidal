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
"""A module containing information and functions related to TIDAL artists."""

import copy
from enum import Enum
from typing import List

import dateutil.parser

IMG_URL = "http://images.osl.wimpmusic.com/im/im?w={width}&h={height}&{id_type}={id}"


class Artist(object):
    id = None
    name = None
    roles = None
    role = None
    picture = None
    user_date_added = None
    bio = None

    def __init__(self, session, artist_id):
        self.session = session
        self.request = self.session.request
        self.id = artist_id
        if artist_id:
            self.request.map_request("artists/%s" % artist_id, parse=self.parse_artist)

    def parse_artist(self, json_obj) -> "Artist":
        """

        :param json_obj:
        :return:
        """
        self.id = json_obj["id"]
        self.name = json_obj["name"]

        # Artists do not have roles as playlist creators.
        self.roles = None
        self.role = None
        if json_obj.get("type") or json_obj.get("artistTypes"):
            roles = []
            for role in json_obj.get("artistTypes", [json_obj.get("type")]):
                roles.append(Role(role))

            self.roles = roles
            self.role = roles[0]

        self.picture = json_obj.get("picture")

        user_date_added = json_obj.get("dateAdded")
        self.user_date_added = (
            dateutil.parser.isoparse(user_date_added) if user_date_added else None
        )

        return copy.copy(self)

    def parse_artists(self, json_obj) -> List["Artist"]:
        """Parses a TIDAL artist, replaces the current artist object. Made for use
        inside of the python tidalapi module.

        :param json_obj: Json data returned from api.tidal.com containing an artist
        :return: Returns a copy of the original :exc: 'Artist': object
        """
        return list(map(self.parse_artist, json_obj))

    def _get_albums(self, params=None):
        return self.request.map_request(
            "artists/%s/albums" % self.id, params, parse=self.session.parse_album
        )

    def get_albums(self, limit=None, offset=0):
        """Queries TIDAL for the artists albums.

        :return: A list of :class:`Albums<tidalapi.album.Album>`
        """
        params = {"limit": limit, "offset": offset}
        return self._get_albums(params)

    def get_albums_ep_singles(self, limit=None, offset=0):
        """Queries TIDAL for the artists extended plays and singles.

        :return: A list of :class:`Albums <tidalapi.album.Album>`
        """
        params = {"filter": "EPSANDSINGLES", "limit": limit, "offset": offset}
        return self._get_albums(params)

    def get_albums_other(self, limit=None, offset=0):
        """Queries TIDAL for albums the artist has appeared on as a featured artist.

        :return: A list of :class:`Albums <tidalapi.album.Album>`
        """
        params = {"filter": "COMPILATIONS", "limit": limit, "offset": offset}
        return self._get_albums(params)

    def get_top_tracks(self, limit=None, offset=0):
        """Queries TIDAL for the artists tracks, sorted by popularity.

        :return: A list of :class:`Tracks <tidalapi.media.Track>`
        """
        params = {"limit": limit, "offset": offset}
        return self.request.map_request(
            "artists/%s/toptracks" % self.id,
            params=params,
            parse=self.session.parse_track,
        )

    def get_videos(self, limit=None, offset=0):
        """Queries tidal for the artists videos.

        :return: A list of :class:`Videos <tidalapi.media.Video>`
        """
        params = {"limit": limit, "offset": offset}
        return self.request.map_request(
            "artists/%s/videos" % self.id, params=params, parse=self.session.parse_video
        )

    def get_bio(self):
        """Queries TIDAL for the artists biography.

        :return: A string containing the bio, as well as identifiers to other TIDAL
            objects inside the bio.
        """
        # morguldir: TODO: Add parsing of wimplinks?
        return self.request.request("GET", "artists/%s/bio" % self.id).json()["text"]

    def get_similar(self):
        """Queries TIDAL for similar artists.

        :return: A list of :class:`Artists <tidalapi.artist.Artist>`
        """
        return self.request.map_request(
            "artists/%s/similar" % self.id, parse=self.parse_artist
        )

    def get_radio(self):
        """Queries TIDAL for the artist radio, which is a mix of tracks that are similar
        to what the artist makes.

        :return: A list of :class:`Tracks <tidalapi.media.Track>`
        """
        params = {"limit": 100}
        return self.request.map_request(
            "artists/%s/radio" % self.id, params=params, parse=self.session.parse_track
        )

    def image(self, dimensions):
        """A url to an artist picture.

        :param dimensions: The width and height that you want from the image
        :type dimensions: int
        :return: A url to the image.

        Valid resolutions: 160x160, 320x320, 480x480, 750x750
        """
        if dimensions not in [160, 320, 480, 750]:
            raise ValueError("Invalid resolution {0} x {0}".format(dimensions))

        if not self.picture:
            json = self.request.request("get", "artists/%s" % self.id).json()
            self.picture = json.get("picture")

        return self.session.config.image_url % (
            self.picture.replace("-", "/"),
            dimensions,
            dimensions,
        )

    def page(self):
        """
        Retrieve the artist page as seen on https://listen.tidal.com/artist/$id

        :return: A :class:`.Page` containing all the categories from the page, e.g. tracks, influencers and credits
        """
        return self.session.page.get("pages/artist", params={"artistId": self.id})


class Role(Enum):
    """An Enum with different roles an artist can have."""

    main = "MAIN"
    featured = "FEATURED"
    contributor = "CONTRIBUTOR"
    artist = "ARTIST"
