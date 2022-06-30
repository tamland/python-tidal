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

"""
A module containing functions relating to TIDAL mixes.
"""
import copy
from enum import Enum


class MixType(Enum):
    """
    An enum to track all the different types of mixes
    """
    video_daily = 'VIDEO_DAILY_MIX'
    daily = 'DAILY_MIX'
    discovery = 'DISCOVERY_MIX'
    new_release = 'NEW_RELEASE_MIX'
    track = 'TRACK_MIX'
    artist = 'ARTIST_MIX'
    songwriter = 'SONGWRITER_MIX'
    producter = 'PRODUCER_MIX'
    history_alltime = 'HISTORY_ALLTIME_MIX'
    history_monthly = 'HISTORY_MONTHLY_MIX'
    history_yearly = 'HISTORY_YEARLY_MIX'


class Mix(object):
    """
    A mix from TIDAL, e.g. the listen.tidal.com/view/pages/my_collection_my_mixes

    These get used for many things, like artist/track radio's, recommendations, and historical plays
    """
    id = ""
    title = ""
    sub_title = ""
    sharing_images = None
    mix_type = None
    content_behaviour = ""
    short_subtitle = ""
    _retrieved = False
    _items = None

    def __init__(self, session, mix_id):
        self.session = session
        self.request = session.request
        if mix_id is not None:
            self.get(mix_id)

    def get(self, mix_id=None):
        """
        Returns information about a mix, and also replaces the mix object used to call this function.

        :param mix_id: TIDAL's identifier of the mix
        :return: A :class:`Mix` object containing all the information about the mix
        """
        if mix_id is None:
            mix_id = self.id

        params = {'mixId': mix_id,
                  'deviceType': 'BROWSER'}
        parse = self.session.parse_page
        result = self.request.map_request('pages/mix', parse=parse, params=params)
        self._retrieved = True
        self.__dict__.update(result.categories[0].__dict__)
        self._items = result.categories[1].items
        return self

    def parse(self, json_obj):
        """ Parse a mix into a :class:`Mix`, replaces the calling object

        :param json_obj: The json of a mix to be parsed
        :return: A copy of the parsed mix
        """
        self.id = json_obj['id']
        self.title = json_obj['title']
        self.sub_title = json_obj['subTitle']
        self.sharing_images = json_obj['sharingImages']
        self.mix_type = MixType(json_obj['mixType'])
        self.content_behaviour = json_obj['contentBehavior']
        self.short_subtitle = json_obj['shortSubtitle']

        return copy.copy(self)

    def items(self):
        """
        Returns all the items in the mix, retrieves them with :class:`get` as well if not already done

        :return: A :class:`list` of videos and/or tracks from the mix
        """
        if not self._retrieved:
            self.get(self.id)

        return self._items
