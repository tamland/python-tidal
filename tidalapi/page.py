# -*- coding: utf-8 -*-

# Copyright (C) 2021-2022 morguldir
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
Module for parsing TIDAL's pages format found at https://listen.tidal.com/v1/pages
"""

import copy
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union, cast

from tidalapi.types import JsonObj

if TYPE_CHECKING:
    import tidalapi


class Page(object):
    """
    A page from the https://listen.tidal.com/view/pages/ endpoint

    The :class:`categories` field will the most complete information
    However it is an iterable that goes through all the visible items on the page as well, in the natural reading order
    """

    title = ""
    categories: Optional[List[Any]] = None
    _categories_iter: Optional[Iterator[Any]] = None

    def __init__(self, session, title):
        self.request = session.request
        self.categories = None
        self.title = title
        self.page_category = PageCategory(session)

    def __iter__(self):
        if self.categories is None:
            raise AttributeError("No categories found")
        self._categories_iter = iter(self.categories)
        self._category = next(self._categories_iter)
        self._items_iter = iter(self._category.items)
        return self

    def __next__(self):
        if self._category == StopIteration:
            return StopIteration
        try:
            item = next(self._items_iter)
        except StopIteration:
            if self._categories_iter is None:
                raise AttributeError("No categories found")
            self._category = next(self._categories_iter)
            self._items_iter = iter(self._category.items)
            return self.__next__()
        return item

    def next(self):
        return self.__next__()

    def parse(self, json_obj: JsonObj) -> "Page":
        """Goes through everything in the page, and gets the title and adds all the rows
        to the categories field :param json_obj: The json to be parsed :return: A copy
        of the Page that you can use to browse all the items."""
        self.title = json_obj["title"]
        self.categories = []
        for row in json_obj["rows"]:
            page_item = self.page_category.parse(row["modules"][0])
            self.categories.append(page_item)

        return copy.copy(self)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> "Page":
        """Retrieve a page from the specified endpoint, overwrites the calling page.

        :param params: Parameter to retrieve the page with
        :param endpoint: The endpoint you want to retrieve
        :return: A copy of the new :class:`.Page` at the requested endpoint
        """
        url = endpoint

        if params is None:
            params = {}
        if "deviceType" not in params:
            params["deviceType"] = "BROWSER"

        json_obj = self.request.request("GET", url, params=params).json()
        return self.parse(json_obj)


class PageCategory(object):
    type = None
    title = None
    description: Optional[str] = ""
    requests = None
    _more: Optional[dict[str, Union[dict[str, str], str]]] = None

    def __init__(self, session: "tidalapi.session.Session"):
        self.session = session
        self.request = session.request
        self.item_types = {
            "ALBUM_LIST": self.session.parse_album,
            "ARTIST_LIST": self.session.parse_artist,
            "TRACK_LIST": self.session.parse_track,
            "PLAYLIST_LIST": self.session.parse_playlist,
            "VIDEO_LIST": self.session.parse_video,
            "MIX_LIST": self.session.parse_mix,
        }

    def parse(self, json_obj):
        result = None
        category_type = json_obj["type"]
        if category_type in ("PAGE_LINKS_CLOUD", "PAGE_LINKS"):
            category: Union[
                PageLinks, FeaturedItems, ItemList, TextBlock, LinkList
            ] = PageLinks(self.session)
        elif category_type in ("FEATURED_PROMOTIONS", "MULTIPLE_TOP_PROMOTIONS"):
            category = FeaturedItems(self.session)
        elif category_type in self.item_types.keys():
            category = ItemList(self.session)
        elif category_type == "MIX_HEADER":
            return self.session.parse_mix(json_obj["mix"])
        elif category_type == "ARTIST_HEADER":
            result = self.session.parse_artist(json_obj["artist"])
            result.bio = json_obj["bio"]
            return result
        elif category_type == "ALBUM_HEADER":
            return self.session.parse_album(json_obj["album"])
        elif category_type == "HIGHLIGHT_MODULE":
            category = ItemList(self.session)
        elif category_type == "MIXED_TYPES_LIST":
            category = ItemList(self.session)
        elif category_type == "TEXT_BLOCK":
            category = TextBlock(self.session)
        elif category_type in ("ITEM_LIST_WITH_ROLES", "ALBUM_ITEMS"):
            category = ItemList(self.session)
        elif category_type == "ARTICLE_LIST":
            json_obj["items"] = json_obj["pagedList"]["items"]
            category = LinkList(self.session)
        elif category_type == "SOCIAL":
            json_obj["items"] = json_obj["socialProfiles"]
            category = LinkList(self.session)
        else:
            raise NotImplementedError(
                "PageType {} not implemented".format(category_type)
            )

        return category.parse(json_obj)

    def show_more(self):
        """Get the full list of items on their own :class:`.Page` from a
        :class:`.PageCategory`

        :return: A :class:`.Page` more of the items in the category, None if there aren't any
        """
        if self._more:
            api_path = self._more["apiPath"]
            assert isinstance(api_path, str)
        else:
            api_path = None
        return (
            Page(self.session, self._more["title"]).get(api_path)
            if api_path and self._more
            else None
        )


class FeaturedItems(PageCategory):
    """Items that have been featured by TIDAL."""

    items: Optional[list["PageItem"]] = None

    def __init__(self, session):
        super(FeaturedItems, self).__init__(session)

    def parse(self, json_obj):
        self.items = []
        self.title = json_obj["title"]
        self.description = json_obj["description"]

        for item in json_obj["items"]:
            self.items.append(PageItem(self.session, item))

        return self


class PageLinks(PageCategory):
    """A list of :class:`.PageLink` to other parts of TIDAL."""

    items: Optional[list["PageLink"]] = None

    def parse(self, json_obj):
        """Parse the list of links from TIDAL.

        :param json_obj: The json to be parsed
        :return: A copy of this page category containing the links in the items field
        """
        self._more = json_obj.get("showMore")
        self.title = json_obj["title"]
        self.items = []
        for item in json_obj["pagedList"]["items"]:
            self.items.append(PageLink(self.session, item))

        return copy.copy(self)


class ItemList(PageCategory):
    """A list of items from TIDAL, can be a list of mixes, for example, or a list of
    playlists and mixes in some cases."""

    items = None

    def parse(self, json_obj):
        """Parse a list of items on TIDAL from the pages endpoints.

        :param json_obj: The json from TIDAL to be parsed
        :return: A copy of the ItemList with a list of items
        """
        self._more = json_obj.get("showMore")
        self.title = json_obj["title"]
        item_type = json_obj["type"]
        list_key = "pagedList"
        session = None
        parse = None

        if item_type in self.item_types.keys():
            parse = self.item_types[item_type]
        elif item_type == "HIGHLIGHT_MODULE":
            session = self.session
            # Unwrap subtitle, maybe add a field for it later
            json_obj[list_key] = {"items": [x["item"] for x in json_obj["highlights"]]}
        elif item_type in ("MIXED_TYPES_LIST", "ALBUM_ITEMS"):
            session = self.session
        elif item_type == "ITEM_LIST_WITH_ROLES":
            for item in json_obj[list_key]["items"]:
                item["item"]["artistRoles"] = item["roles"]
            session = self.session
        else:
            raise NotImplementedError("PageType {} not implemented".format(item_type))

        self.items = self.request.map_json(json_obj[list_key], parse, session)

        return copy.copy(self)


class PageLink(object):
    """A Link to another :class:`.Page` on TIDAL, Call get() to retrieve the Page."""

    title = None
    icon = None
    image_id = None
    requests = None

    def __init__(self, session: "tidalapi.session.Session", json_obj):
        self.session = session
        self.request = session.request
        self.title = json_obj["title"]
        self.icon = json_obj["icon"]
        self.api_path = cast(str, json_obj["apiPath"])
        self.image_id = json_obj["imageId"]

    def get(self):
        """Requests the linked page from TIDAL :return: A :class:`Page` at the
        api_path."""
        return self.request.map_request(
            self.api_path,
            params={"deviceType": "DESKTOP"},
            parse=self.session.parse_page,
        )


class PageItem(object):
    """An Item from a :class:`.PageCategory` from the /pages endpoint, call get() to
    retrieve the actual item."""

    header = ""
    short_header = ""
    short_sub_header = ""
    image_id = ""
    type = ""
    artifact_id = ""
    text = ""
    featured = False

    def __init__(self, session, json_obj):
        self.session = session
        self.request = session.request
        self.header = json_obj["header"]
        self.short_header = json_obj["shortHeader"]
        self.short_sub_header = json_obj["shortSubHeader"]
        self.image_id = json_obj["imageId"]
        self.type = json_obj["type"]
        self.artifact_id = json_obj["artifactId"]
        self.text = json_obj["text"]
        self.featured = bool(json_obj["featured"])

    def get(self):
        """Retrieve the PageItem with the artifact_id matching the type.

        :return: The fully parsed item, e.g. :class:`.Playlist`, :class:`.Video`, :class:`.Track`
        """
        if self.type == "PLAYLIST":
            result = self.session.playlist(self.artifact_id)
        elif self.type == "VIDEO":
            result = self.session.video(self.artifact_id)
        elif self.type == "TRACK":
            result = self.session.track(self.artifact_id)
        elif self.type == "ARTIST":
            result = self.session.artist(self.artifact_id)
        else:
            raise NotImplementedError("PageItem type %s not implemented" % self.type)

        return result


class TextBlock(object):
    """A block of text, with a named icon, which seems to be left up to the
    application."""

    text = ""
    icon = ""
    items = None

    def __init__(self, session):
        self.session = session

    def parse(self, json_obj):
        self.text = json_obj["text"]
        self.icon = json_obj["icon"]
        self.items = [self.text]

        return copy.copy(self)


class LinkList(PageCategory):
    """A list of items containing links, e.g. social links or articles."""

    items = None
    title = None
    description = None

    def parse(self, json_obj):
        self.items = json_obj["items"]
        self.title = json_obj["title"]
        self.description = json_obj["description"]

        return copy.copy(self)
