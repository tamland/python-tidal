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
from typing import TYPE_CHECKING, List, Optional, Sequence, Union

from tidalapi.exceptions import ObjectNotFound, TooManyRequests
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

    # Direct URL to https://listen.tidal.com/playlist/<playlist_id>
    listen_url: str = ""
    # Direct URL to https://tidal.com/browse/playlist/<playlist_id>
    share_url: str = ""

    def __init__(self, session: "Session", playlist_id: Optional[str]):
        self.id = playlist_id
        self.session = session
        self.request = session.request
        self._base_url = "playlists/%s"
        if playlist_id:
            try:
                request = self.request.request("GET", self._base_url % self.id)
            except ObjectNotFound:
                raise ObjectNotFound("Playlist not found")
            except TooManyRequests:
                raise TooManyRequests("Playlist unavailable")
            else:
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

        self.listen_url = f"{self.session.config.listen_base_url}/playlist/{self.id}"
        self.share_url = f"{self.session.config.share_base_url}/playlist/{self.id}"

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
        request = self.request.request(
            "GET", self._base_url % self.id + "/tracks", params=params
        )
        self._etag = request.headers["etag"]
        return list(
            self.request.map_json(
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
        request = self.request.request(
            "GET", self._base_url % self.id + "/items", params=params
        )
        self._etag = request.headers["etag"]
        return list(
            self.request.map_json(request.json(), parse=self.session.parse_media)
        )

    def image(self, dimensions: int = 480, wide_fallback: bool = True) -> str:
        """A URL to a playlist picture.

        :param dimensions: The width and height that want from the image
        :type dimensions: int
        :param wide_fallback: Use wide image as fallback if no square cover picture exists
        :type wide_fallback: bool
        :return: A url to the image

        Original sizes: 160x160, 320x320, 480x480, 640x640, 750x750, 1080x1080
        """

        if dimensions not in [160, 320, 480, 640, 750, 1080]:
            raise ValueError("Invalid resolution {0} x {0}".format(dimensions))
        if self.square_picture:
            return self.session.config.image_url % (
                self.square_picture.replace("-", "/"),
                dimensions,
                dimensions,
            )
        elif self.picture and wide_fallback:
            return self.wide_image()
        else:
            raise AttributeError("No picture available")

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
        # Re-Read Playlist to get ETag
        request = self.request.request("GET", self._base_url % self.id)
        self._etag = request.headers["etag"]
        self.request.map_json(request.json(), parse=self.parse)

    def edit(
        self, title: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        """
        Edit UserPlaylist title & description
        :param title: Playlist title
        :param description: Playlist title
        """
        if not title:
            title = self.name
        if not description:
            description = self.description

        data = {"title": title, "description": description}
        self.request.request("POST", self._base_url % self.id, data=data)

    def delete(self, media_ids: List[str]) -> None:
        """
        Delete one or more items from the UserPlaylist
        :param media_ids: Lists of Media IDs to remove
        """
        # Generate list of track indices of tracks found in the list of media_ids.
        track_ids = [str(track.id) for track in self.tracks()]
        matching_indices = [i for i, item in enumerate(track_ids) if item in media_ids]
        self.remove_by_indices(matching_indices)

    def add(self, media_ids: List[str]) -> None:
        """
        Add one or more items to the UserPlaylist
        :param media_ids: List of Media IDs to add
        """
        data = {
            "onArtifactNotFound": "SKIP",
            "onDupes": "SKIP",
            "trackIds": ",".join(map(str, media_ids)),
        }
        params = {"limit": 100}
        headers = {"If-None-Match": self._etag} if self._etag else None
        self.request.request(
            "POST",
            self._base_url % self.id + "/items",
            params=params,
            data=data,
            headers=headers,
        )
        self._reparse()

    def remove_by_id(self, media_id: str) -> None:
        """
        Remove a single item from the playlist, using the media ID
        :param media_id: Media ID to remove
        """
        track_ids = [str(track.id) for track in self.tracks()]
        try:
            index = track_ids.index(media_id)
            if index is not None and index < self.num_tracks:
                self.remove_by_index(index)
        except ValueError:
            pass

    def remove_by_index(self, index: int) -> None:
        """
        Remove a single item from the UserPlaylist, using item index.
        :param index: Media index to remove
        """
        headers = {"If-None-Match": self._etag} if self._etag else None
        self.request.request(
            "DELETE", (self._base_url + "/items/%i") % (self.id, index), headers=headers
        )

    def remove_by_indices(self, indices: Sequence[int]) -> None:
        """
        Remove one or more items from the UserPlaylist, using list of indices
        :param indices: List containing indices to remove
        """
        headers = {"If-None-Match": self._etag} if self._etag else None
        track_index_string = ",".join([str(x) for x in indices])
        self.request.request(
            "DELETE",
            (self._base_url + "/items/%s") % (self.id, track_index_string),
            headers=headers,
        )
        self._reparse()

    def clear(self, chunk_size: int = 50):
        """
        Clear UserPlaylist
        :param chunk_size: Number of items to remove per request
        :return:
        """
        while self.num_tracks:
            indices = range(min(self.num_tracks, chunk_size))
            self.remove_by_indices(indices)

    def set_playlist_public(self):
        """
        Set UserPlaylist as Public
        """
        self.request.request(
            "PUT",
            base_url=self.session.config.api_v2_location,
            path=(self._base_url + "/set-public") % self.id,
        )
        self.public = True
        self._reparse()

    def set_playlist_private(self):
        """
        Set UserPlaylist as Private
        """
        self.request.request(
            "PUT",
            base_url=self.session.config.api_v2_location,
            path=(self._base_url + "/set-private") % self.id,
        )
        self.public = False
        self._reparse()

    def delete_playlist(self):
        """
        Delete UserPlaylist
        :return: True, if successful
        """
        return self.request.request("DELETE", path="playlists/%s" % self.id).ok
