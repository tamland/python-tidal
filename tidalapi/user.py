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
"""A module containing classes and functions related to tidal users.

:class:`User` is a class with user information.
:class:`Favorites` is class with a users favorites.
"""

from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING, Dict, List, Optional, Union, cast
from urllib.parse import urljoin

from tidalapi.types import JsonObj

if TYPE_CHECKING:
    from tidalapi.album import Album
    from tidalapi.artist import Artist
    from tidalapi.media import Track, Video
    from tidalapi.mix import MixV2
    from tidalapi.playlist import Playlist, UserPlaylist
    from tidalapi.session import Session


class User:
    """A class containing various information about a TIDAL user.

    The attributes of this class are pretty varied. ID is the only attribute you can
    rely on being set. If you initialized a specific user, you will get id, first_name,
    last_name, and picture_id. If parsed as a playlist creator, you will get an ID and a
    name, if the creator isn't an artist, name will be 'user'. If the parsed user is the
    one logged in, for example in session.user, you will get the remaining attributes,
    and id.
    """

    id: Optional[int] = -1

    def __init__(self, session: "Session", user_id: Optional[int]):
        self.id = user_id
        self.session = session
        self.request = session.request
        self.playlist = session.playlist()

    def factory(self) -> Union["LoggedInUser", "FetchedUser", "PlaylistCreator"]:
        return cast(
            Union["LoggedInUser", "FetchedUser", "PlaylistCreator"],
            self.request.map_request("users/%s" % self.id, parse=self.parse),
        )

    def parse(
        self, json_obj: JsonObj
    ) -> Union["LoggedInUser", "FetchedUser", "PlaylistCreator"]:
        if "username" in json_obj:
            user: Union[LoggedInUser, FetchedUser, PlaylistCreator] = LoggedInUser(
                self.session, json_obj["id"]
            )

        elif "firstName" in json_obj:
            user = FetchedUser(self.session, json_obj["id"])

        elif json_obj:
            user = PlaylistCreator(self.session, json_obj["id"])

        # When searching TIDAL does not show up as a creator in the json data.
        else:
            user = PlaylistCreator(self.session, 0)

        return user.parse(json_obj)


class FetchedUser(User):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture_id: Optional[str] = None

    def parse(self, json_obj: JsonObj) -> "FetchedUser":
        self.id = json_obj["id"]
        self.first_name = json_obj["firstName"]
        self.last_name = json_obj["lastName"]
        self.picture_id = json_obj.get("picture", None)

        return copy(self)

    def image(self, dimensions: int) -> str:
        if dimensions not in [100, 210, 600]:
            raise ValueError("Invalid resolution {0} x {0}".format(dimensions))

        if self.picture_id is None:
            raise AttributeError("No picture available")

        return self.session.config.image_url % (
            self.picture_id.replace("-", "/"),
            dimensions,
            dimensions,
        )


class LoggedInUser(FetchedUser):
    username: Optional[str] = None
    email: Optional[str] = None
    profile_metadata: Optional[JsonObj] = None

    def __init__(self, session: "Session", user_id: Optional[int]):
        super(LoggedInUser, self).__init__(session, user_id)
        assert self.id is not None, "User is not logged in"
        self.favorites = Favorites(session, self.id)

    def parse(self, json_obj: JsonObj) -> "LoggedInUser":
        super(LoggedInUser, self).parse(json_obj)
        self.username = json_obj["username"]
        self.email = json_obj["email"]
        self.profile_metadata = json_obj

        return copy(self)

    def playlists(self) -> List[Union["Playlist", "UserPlaylist"]]:
        """Get the playlists created by the user.

        :return: Returns a list of :class:`~tidalapi.playlist.Playlist` objects containing the playlists.
        """
        return cast(
            List[Union["Playlist", "UserPlaylist"]],
            self.request.map_request(
                "users/%s/playlists" % self.id, parse=self.playlist.parse_factory
            ),
        )

    def playlist_and_favorite_playlists(
        self, offset: int = 0
    ) -> List[Union["Playlist", "UserPlaylist"]]:
        """Get the playlists created by the user, and the playlists favorited by the
        user. This function is limited to 50 by TIDAL, requiring pagination.

        :return: Returns a list of :class:`~tidalapi.playlist.Playlist` objects containing the playlists.
        """
        params = {"limit": 50, "offset": offset}
        endpoint = "users/%s/playlistsAndFavoritePlaylists" % self.id
        json_obj = self.request.request("GET", endpoint, params=params).json()

        # This endpoint sorts them into favorited and created playlists, but we already do that when parsing them.
        for index, item in enumerate(json_obj["items"]):
            item["playlist"]["dateAdded"] = item["created"]
            json_obj["items"][index] = item["playlist"]

        return cast(
            List[Union["Playlist", "UserPlaylist"]],
            self.request.map_json(json_obj, parse=self.playlist.parse_factory),
        )

    def create_playlist(self, title: str, description: str) -> "Playlist":
        data = {"title": title, "description": description}
        json = self.request.request(
            "POST", "users/%s/playlists" % self.id, data=data
        ).json()
        playlist = self.session.playlist().parse(json)
        return playlist.factory()


class PlaylistCreator(User):
    name: Optional[str] = None

    def parse(self, json_obj: JsonObj) -> "PlaylistCreator":
        if self.id == 0 or self.session.user is None:
            self.name = "TIDAL"

        elif "name" in json_obj:
            self.name = json_obj["name"]

        elif self.id == self.session.user.id:
            self.name = "me"

        else:
            self.name = "user"

        return copy(self)


class Favorites:
    """An object containing a users favourites."""

    def __init__(self, session: "Session", user_id: int):
        self.session = session
        self.requests = session.request
        self.base_url = f"users/{user_id}/favorites"
        self.v2_base_url = "favorites"

    def add_album(self, album_id: str) -> bool:
        """Adds an album to the users favorites.

        :param album_id: TIDAL's identifier of the album.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request(
            "POST", f"{self.base_url}/albums", data={"albumId": album_id}
        ).ok

    def add_artist(self, artist_id: str) -> bool:
        """Adds an artist to the users favorites.

        :param artist_id: TIDAL's identifier of the artist
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request(
            "POST", f"{self.base_url}/artists", data={"artistId": artist_id}
        ).ok

    def add_playlist(self, playlist_id: str) -> bool:
        """Adds a playlist to the users favorites.

        :param playlist_id: TIDAL's identifier of the playlist.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request(
            "POST", f"{self.base_url}/playlists", data={"uuids": playlist_id}
        ).ok

    def add_track(self, track_id: str) -> bool:
        """Adds a track to the users favorites.

        :param track_id: TIDAL's identifier of the track.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request(
            "POST", f"{self.base_url}/tracks", data={"trackId": track_id}
        ).ok

    def add_video(self, video_id: str) -> bool:
        """Adds a video to the users favorites.

        :param video_id: TIDAL's identifier of the video.
        :return: A boolean indicating whether the request was successful or not.
        """
        params = {"limit": "100"}
        return self.requests.request(
            "POST",
            f"{self.base_url}/videos",
            data={"videoIds": video_id},
            params=params,
        ).ok

    def remove_artist(self, artist_id: str) -> bool:
        """Removes a track from the users favorites.

        :param artist_id: TIDAL's identifier of the artist.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request(
            "DELETE", f"{self.base_url}/artists/{artist_id}"
        ).ok

    def remove_album(self, album_id: str) -> bool:
        """Removes an album from the users favorites.

        :param album_id: TIDAL's identifier of the album
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request("DELETE", f"{self.base_url}/albums/{album_id}").ok

    def remove_playlist(self, playlist_id: str) -> bool:
        """Removes a playlist from the users favorites.

        :param playlist_id: TIDAL's identifier of the playlist.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request(
            "DELETE", f"{self.base_url}/playlists/{playlist_id}"
        ).ok

    def remove_track(self, track_id: str) -> bool:
        """Removes a track from the users favorites.

        :param track_id: TIDAL's identifier of the track.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request("DELETE", f"{self.base_url}/tracks/{track_id}").ok

    def remove_video(self, video_id: str) -> bool:
        """Removes a video from the users favorites.

        :param video_id: TIDAL's identifier of the video.
        :return: A boolean indicating whether the request was successful or not.
        """
        return self.requests.request("DELETE", f"{self.base_url}/videos/{video_id}").ok

    def artists(self, limit: Optional[int] = None, offset: int = 0) -> List["Artist"]:
        """Get the users favorite artists.

        :return: A :class:`list` of :class:`~tidalapi.artist.Artist` objects containing the favorite artists.
        """
        params = {"limit": limit, "offset": offset}
        return cast(
            List["Artist"],
            self.requests.map_request(
                f"{self.base_url}/artists",
                params=params,
                parse=self.session.parse_artist,
            ),
        )

    def albums(self, limit: Optional[int] = None, offset: int = 0) -> List["Album"]:
        """Get the users favorite albums.

        :return: A :class:`list` of :class:`~tidalapi.album.Album` objects containing the favorite albums.
        """
        params = {"limit": limit, "offset": offset}
        return cast(
            List["Album"],
            self.requests.map_request(
                f"{self.base_url}/albums", params=params, parse=self.session.parse_album
            ),
        )

    def playlists(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List["Playlist"]:
        """Get the users favorite playlists.

        :return: A :class:`list` :class:`~tidalapi.playlist.Playlist` objects containing the favorite playlists.
        """
        params = {"limit": limit, "offset": offset}
        return cast(
            List["Playlist"],
            self.requests.map_request(
                f"{self.base_url}/playlists",
                params=params,
                parse=self.session.parse_playlist,
            ),
        )

    def tracks(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        order: str = "NAME",
        order_direction: str = "ASC",
    ) -> List["Track"]:
        """Get the users favorite tracks.

        :param limit: Optional; The amount of items you want returned.
        :param offset: The index of the first item you want included.
        :param order: A :class:`str` describing the ordering type when returning the user favorite tracks. eg.: "NAME, "DATE"
        :param order_direction: A :class:`str` describing the ordering direction when sorting by `order`. eg.: "ASC", "DESC"
        :return: A :class:`list` of :class:`~tidalapi.media.Track` objects containing all of the favorite tracks.
        """
        params = {
            "limit": limit,
            "offset": offset,
            "order": order,
            "orderDirection": order_direction,
        }

        return cast(
            List["Track"],
            self.requests.map_request(
                f"{self.base_url}/tracks", params=params, parse=self.session.parse_track
            ),
        )

    def videos(self) -> List["Video"]:
        """Get the users favorite videos.

        :return: A :class:`list` of :class:`~tidalapi.media.Video` objects containing all the favorite videos
        """
        return cast(
            List["Video"],
            self.requests.get_items(
                f"{self.base_url}/videos", parse=self.session.parse_media
            ),
        )

    def mixes(self, limit: Optional[int] = 50, offset: int = 0) -> List["MixV2"]:
        """Get the users favorite tracks.

        :return: A :class:`list` of :class:`~tidalapi.media.Track` objects containing all of the favorite tracks.
        """
        params = {"limit": limit, "offset": offset}
        return cast(
            List["MixV2"],
            self.requests.map_request(
                url=urljoin("https://api.tidal.com/v2/", f"{self.v2_base_url}/mixes"),
                params=params,
                parse=self.session.parse_v2_mix,
            ),
        )
