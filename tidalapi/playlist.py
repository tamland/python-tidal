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
"""A module containing things related to TIDAL playlists."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Sequence, Union, cast

from tidalapi.types import JsonObj
from tidalapi.user import LoggedInUser

if TYPE_CHECKING:
    from tidalapi.artist import Artist
    from tidalapi.media import Track, Video
    from tidalapi.session import Session
    from tidalapi.user import User

import dateutil.parser


class Playlist:
    """An object containing various data about a playlist and methods to work with
    them."""

    id: Optional[str] = None
    name: Optional[str] = None
    num_tracks: int = -1
    num_videos: int = -1
    creator: Optional[Union["Artist", "User"]] = None
    description: Optional[str] = None
    duration: int = -1
    last_updated: Optional[datetime] = None
    created: Optional[datetime] = None
    type = None
    public: Optional[bool] = False
    popularity: Optional[int] = None
    promoted_artists: Optional[List["Artist"]] = None
    last_item_added_at: Optional[datetime] = None
    picture: Optional[str] = None
    square_picture: Optional[str] = None
    user_date_added: Optional[datetime] = None
    _etag: Optional[str] = None

    def __init__(self, session: "Session", playlist_id: Optional[str]):
        self.id = playlist_id
        self.session = session
        self.requests = session.request
        self._base_url = "playlists/%s"
        if playlist_id:
            request = self.requests.request("GET", self._base_url % playlist_id)
            self._etag = request.headers["etag"]
            self.parse(request.json())

    def parse(self, json_obj: JsonObj) -> "Playlist":
        """Parses a playlist from tidal, replaces the current playlist object.

        :param json_obj: Json data returned from api.tidal.com containing a playlist
        :return: Returns a copy of the original :exc: 'Playlist': object
        """
        self.id = json_obj["uuid"]
        self.name = json_obj["title"]
        self.num_tracks = int(json_obj["numberOfTracks"])
        self.num_videos = int(json_obj["numberOfVideos"])
        self.description = json_obj["description"]
        self.duration = int(json_obj["duration"])

        # These can be missing on from the /pages endpoints
        last_updated = json_obj.get("lastUpdated")
        self.last_updated = (
            dateutil.parser.isoparse(last_updated) if last_updated else None
        )
        created = json_obj.get("created")
        self.created = dateutil.parser.isoparse(created) if created else None
        public = json_obj.get("publicPlaylist")
        self.public = None if public is None else bool(public)
        popularity = json_obj.get("popularity")
        self.popularity = int(popularity) if popularity else None

        self.type = json_obj["type"]
        self.picture = json_obj["image"]
        self.square_picture = json_obj["squareImage"]

        promoted_artists = json_obj["promotedArtists"]
        self.promoted_artists = (
            self.session.parse_artists(promoted_artists) if promoted_artists else None
        )

        last_item_added_at = json_obj.get("lastItemAddedAt")
        self.last_item_added_at = (
            dateutil.parser.isoparse(last_item_added_at) if last_item_added_at else None
        )

        user_date_added = json_obj.get("dateAdded")
        self.user_date_added = (
            dateutil.parser.isoparse(user_date_added) if user_date_added else None
        )

        creator = json_obj.get("creator")
        if self.type == "ARTIST" and creator and creator.get("id"):
            self.creator = self.session.parse_artist(creator)
        else:
            self.creator = self.session.parse_user(creator) if creator else None

        return copy.copy(self)

    def factory(self) -> "Playlist":
        if (
            self.id
            and self.creator
            and isinstance(self.session.user, LoggedInUser)
            and self.creator.id == self.session.user.id
        ):
            return UserPlaylist(self.session, self.id)

        return self

    def parse_factory(self, json_obj: JsonObj) -> "Playlist":
        self.parse(json_obj)
        return copy.copy(self.factory())

    def tracks(self, limit: Optional[int] = None, offset: int = 0) -> List["Track"]:
        """Gets the playlists' tracks from TIDAL.

        :param limit: The amount of items you want returned.
        :param offset: The index of the first item you want included.
        :return: A list of :class:`Tracks <.Track>`
        """
        params = {"limit": limit, "offset": offset}
        request = self.requests.request(
            "GET", self._base_url % self.id + "/tracks", params=params
        )
        self._etag = request.headers["etag"]
        return list(
            self.requests.map_json(
                json_obj=request.json(), parse=self.session.parse_track
            )
        )

    def items(self, limit: int = 100, offset: int = 0) -> List[Union["Track", "Video"]]:
        """Fetches up to the first 100 items, including tracks and videos.

        :param limit: The amount of items you want, up to 100.
        :param offset: The index of the first item you want returned
        :return: A list of :class:`Tracks<.Track>` and :class:`Videos<.Video>`
        """
        params = {"limit": limit, "offset": offset}
        request = self.requests.request(
            "GET", self._base_url % self.id + "/items", params=params
        )
        self._etag = request.headers["etag"]
        return list(
            self.requests.map_json(request.json(), parse=self.session.parse_media)
        )

    def image(self, dimensions: int = 480) -> str:
        """A URL to a playlist picture.

        :param dimensions: The width and height that want from the image
        :type dimensions: int
        :return: A url to the image

        Original sizes: 160x160, 320x320, 480x480, 640x640, 750x750, 1080x1080
        """

        if dimensions not in [160, 320, 480, 640, 750, 1080]:
            raise ValueError("Invalid resolution {0} x {0}".format(dimensions))
        if self.square_picture is None:
            raise AttributeError("No picture available")
        return self.session.config.image_url % (
            self.square_picture.replace("-", "/"),
            dimensions,
            dimensions,
        )

    def wide_image(self, width: int = 1080, height: int = 720) -> str:
        """Create a url to a wider playlist image.

        :param width: The width of the image
        :param height: The height of the image
        :return: Returns a url to the image with the specified resolution

        Valid sizes: 160x107, 480x320, 750x500, 1080x720
        """

        if (width, height) not in [(160, 107), (480, 320), (750, 500), (1080, 720)]:
            raise ValueError("Invalid resolution {} x {}".format(width, height))
        if self.picture is None:
            raise AttributeError("No picture available")
        return self.session.config.image_url % (
            self.picture.replace("-", "/"),
            width,
            height,
        )


class UserPlaylist(Playlist):
    def _reparse(self) -> None:
        request = self.requests.request("GET", self._base_url % self.id)
        self._etag = request.headers["etag"]
        self.requests.map_json(request.json(), parse=self.parse)

    def edit(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        if not title:
            title = self.name
        if not description:
            description = self.description

        data = {"title": title, "description": description}
        self.requests.request("POST", self._base_url % self.id, data=data)

    def delete(self) -> None:
        self.requests.request("DELETE", self._base_url % self.id)

    def add(self, media_ids: List[str]) -> None:
        data = {
            "onArtifactNotFound": "SKIP",
            "onDupes": "SKIP",
            "trackIds": ",".join(map(str, media_ids)),
        }
        params = {"limit": 100}
        headers = {"If-None-Match": self._etag} if self._etag else None
        self.requests.request(
            "POST",
            self._base_url % self.id + "/items",
            params=params,
            data=data,
            headers=headers,
        )
        self._reparse()

    def remove_by_index(self, index: int) -> None:
        headers = {"If-None-Match": self._etag} if self._etag else None
        self.requests.request(
            "DELETE", (self._base_url + "/items/%i") % (self.id, index), headers=headers
        )

    def remove_by_indices(self, indices: Sequence[int]) -> None:
        headers = {"If-None-Match": self._etag} if self._etag else None
        track_index_string = ",".join([str(x) for x in indices])
        self.requests.request(
            "DELETE",
            (self._base_url + "/tracks/%s") % (self.id, track_index_string),
            headers=headers,
        )

    def _calculate_id(self, media_id: str) -> Optional[int]:
        i = 0
        while i < self.num_tracks:
            items = self.items(100, i)
            for index, item in enumerate(items):
                if item.id == media_id:
                    # Return the amount of items we have gone through plus the index in the last list.
                    return index + i

            i += len(items)
        return None

    def remove_by_id(self, media_id: str) -> None:
        index = self._calculate_id(media_id)
        if index is not None:
            self.remove_by_index(index)
