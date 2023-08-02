# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 morguldir
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
"""A module containing functions relating to TIDAL mixes."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Union

from tidalapi.types import JsonObj

if TYPE_CHECKING:
    from tidalapi.media import Track, Video
    from tidalapi.session import Session


class MixType(Enum):
    """An enum to track all the different types of mixes."""

    video_daily = "VIDEO_DAILY_MIX"
    daily = "DAILY_MIX"
    discovery = "DISCOVERY_MIX"
    new_release = "NEW_RELEASE_MIX"
    track = "TRACK_MIX"
    artist = "ARTIST_MIX"
    songwriter = "SONGWRITER_MIX"
    producter = "PRODUCER_MIX"
    history_alltime = "HISTORY_ALLTIME_MIX"
    history_monthly = "HISTORY_MONTHLY_MIX"
    history_yearly = "HISTORY_YEARLY_MIX"


@dataclass
class ImageResponse:
    small: str
    medium: str
    large: str


class Mix:
    """A mix from TIDAL, e.g. the listen.tidal.com/view/pages/my_collection_my_mixes.

    These get used for many things, like artist/track radio's, recommendations, and
    historical plays
    """

    id: str = ""
    title: str = ""
    sub_title: str = ""
    sharing_images = None
    mix_type: Optional[MixType] = None
    content_behaviour: str = ""
    short_subtitle: str = ""
    images: Optional[ImageResponse] = None
    _retrieved = False
    _items: Optional[List[Union["Video", "Track"]]] = None

    def __init__(self, session: Session, mix_id: str):
        self.session = session
        self.request = session.request
        if mix_id is not None:
            self.get(mix_id)

    def get(self, mix_id: Optional[str] = None) -> "Mix":
        """Returns information about a mix, and also replaces the mix object used to
        call this function.

        :param mix_id: TIDAL's identifier of the mix
        :return: A :class:`Mix` object containing all the information about the mix
        """
        if mix_id is None:
            mix_id = self.id

        params = {"mixId": mix_id, "deviceType": "BROWSER"}
        parse = self.session.parse_page
        result = self.request.map_request("pages/mix", parse=parse, params=params)
        assert not isinstance(result, list)
        self._retrieved = True
        self.__dict__.update(result.categories[0].__dict__)
        self._items = result.categories[1].items
        return self

    def parse(self, json_obj: JsonObj) -> "Mix":
        """Parse a mix into a :class:`Mix`, replaces the calling object.

        :param json_obj: The json of a mix to be parsed
        :return: A copy of the parsed mix
        """
        self.id = json_obj["id"]
        self.title = json_obj["title"]
        self.sub_title = json_obj["subTitle"]
        self.sharing_images = json_obj["sharingImages"]
        self.mix_type = MixType(json_obj["mixType"])
        self.content_behaviour = json_obj["contentBehavior"]
        self.short_subtitle = json_obj["shortSubtitle"]
        images = json_obj["images"]
        self.images = ImageResponse(
            small=images["SMALL"]["url"],
            medium=images["MEDIUM"]["url"],
            large=images["LARGE"]["url"],
        )

        return copy.copy(self)

    def items(self) -> List[Union["Video", "Track"]]:
        """Returns all the items in the mix, retrieves them with :class:`get` as well if
        not already done.

        :return: A :class:`list` of videos and/or tracks from the mix
        """
        if not self._retrieved:
            self.get(self.id)
        if not self._items:
            raise ValueError("Retrieved items missing")
        return self._items

    def image(self, dimensions: int) -> str:
        """A URL to a Mix picture.

        :param dimensions: The width and height the requested image should be
        :type dimensions: int
        :return: A url to the image

        Original sizes: 320x320, 640x640, 1500x1500
        """
        if not self.images:
            raise ValueError("No images present.")

        if dimensions == 320:
            return self.images.small
        elif dimensions == 640:
            return self.images.medium
        elif dimensions == 1500:
            return self.images.large

        raise ValueError(f"Invalid resolution {dimensions} x {dimensions}")
