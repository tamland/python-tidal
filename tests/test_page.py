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
from future.builtins import isinstance, str

import tidalapi


def test_home(session):
    home = session.home()
    assert home


def test_explore(session):
    explore = session.explore()
    assert explore


def test_get_explore_items(session):
    explore = session.explore()
    iterator = iter(explore)
    playlist = next(iterator).get()
    assert playlist.name
    assert playlist.num_tracks > 1

    genre = explore.categories[1].items[0]
    genre_page_items = iter(genre.get())
    assert isinstance(next(genre_page_items).get(), tidalapi.Playlist)

    genres = explore.categories[1].show_more()
    iterator = iter(genres)
    next(iterator)
    assert next(iterator).title == 'Africa'
    assert next(iterator).title == 'Blues'


def test_show_more(session):
    videos = session.videos()
    originals = next(iter(filter(lambda x: x.title == 'TIDAL Originals', videos.categories)))
    more = originals.show_more()
    assert len(more.categories[0].items) > 0
    assert isinstance(next(iter(more)), tidalapi.Artist)


def test_page_iterator(session):
    video_page = session.videos()
    playlists = 0
    videos = 0
    for item in video_page:
        if isinstance(item, tidalapi.Playlist):
            playlists += 1
        elif isinstance(item, tidalapi.Video):
            videos += 1

    assert playlists > 20
    assert videos > 20


def test_get_video_items(session):
    videos = session.videos()
    mix = videos.categories[1].items[0].get()
    for item in mix.items():
        assert isinstance(item, tidalapi.Video)

    assert len(mix.items()) >= 25


def test_page_links(session):
    explore = session.explore()
    for item in explore.categories[3].items:
        page = item.get()
        if item.title == 'TIDAL Rising':
            assert isinstance(page.categories[1].text, str)


def test_genres(session):
    genres = session.genres()
    first = next(iter(genres))
    assert first.title == "Africa"
    assert isinstance(next(iter(first.get())), tidalapi.Playlist)

    local_genres = session.local_genres()
    first_local = next(iter(local_genres))
    assert first_local != first
    assert isinstance(next(iter(first_local.get())).get(), tidalapi.Playlist)


def test_moods(session):
    moods = session.moods()
    first = next(iter(moods))
    assert first.title == 'Music School'
    assert isinstance(next(iter(first.get())), tidalapi.Playlist)


def test_mixes(session):
    mixes = session.mixes()
    first = next(iter(mixes))
    assert first.title == "My Daily Discovery"
    assert len(first.items()) == 10


def test_artist_page(session):
    page = session.artist(3503597).page()
    for category in page.categories:
        if hasattr(category, "title") and category.title == "Influencers":
            for artist in category.items:
                assert artist.page()
    assert page


def test_album_page(session):
    page = session.album(108043414).page()
    for category in page.categories:
        if hasattr(category, "title") and category.title == "Related Albums":
            for item in category.items:
                assert item.page()
    assert page
