# -*- coding: utf-8 -*-
#
# Copyright (C) 2023- The Tidalapi Developers
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

import tidalapi


def test_home(session):
    home = session.home()
    assert home


def test_explore(session):
    explore = session.explore()
    assert explore


def test_get_explore_items(session):
    explore = session.explore()
    assert explore.title == "Explore"
    # First page usually contains Genres
    assert explore.categories[0].title == "Genres"
    assert explore.categories[1].title == "Moods, Activities & Events"
    assert explore.categories[2].title == ""  # Usually empty

    # Genre_decades items
    genre_decades = explore.categories[0].items[0]
    genre_decades_page_items = iter(genre_decades.get())
    first_item = next(genre_decades_page_items).get()
    assert isinstance(first_item, tidalapi.Page)
    assert first_item.title == "1950s"
    assert first_item.categories[0].title == "Playlists"
    assert first_item.categories[1].title == "Milestone Year Albums"
    assert first_item.categories[2].title == "Albums Of The Decade"
    playlist = first_item.categories[0].items[0]
    assert isinstance(playlist, tidalapi.Playlist)
    assert playlist.name  # == 'Remember...the 1950s'
    assert playlist.num_tracks > 1
    assert playlist.num_videos == 0

    genre_genres = explore.categories[0].items[1]
    genre_genres_page_items = iter(genre_genres.get())
    playlist = next(genre_genres_page_items)  # Usually a playlist
    assert isinstance(playlist, tidalapi.Playlist)
    assert playlist.name  # == 'Remember...the 1950s'
    assert playlist.num_tracks > 1
    assert playlist.num_videos == 0

    genres_more = explore.categories[0].show_more()
    iterator = iter(genres_more)
    next(iterator)
    assert next(iterator).title == "Classical"
    assert next(iterator).title == "Country"


def test_hires_page(session):
    hires = session.hires_page()
    first = next(iter(hires))
    assert first.name == "Electronic: Headphone Classics"
    assert isinstance(first, tidalapi.Playlist)


def test_for_you(session):
    for_you = session.for_you()
    first = next(iter(for_you))
    assert first.title == "My Daily Discovery"
    assert isinstance(first, tidalapi.Mix)


def test_videos(session):
    videos = session.videos()
    first = next(iter(videos))
    assert first.type == "VIDEO"
    assert isinstance(first.get(), tidalapi.Video)


def test_show_more(session):
    videos = session.videos()
    originals = next(
        iter(filter(lambda x: x.title == "Custom mixes", videos.categories))
    )
    more = originals.show_more()
    assert len(more.categories[0].items) > 0
    assert isinstance(next(iter(more)), tidalapi.Mix)


def test_page_iterator(session):
    video_page = session.videos()
    playlists = 0
    videos = 0
    for item in video_page:
        if isinstance(item, tidalapi.Playlist):
            playlists += 1
        elif isinstance(item, tidalapi.Video):
            videos += 1

    # Number of playlists tend to change, resulting in failing tests.
    # So we will make sure at least 10 playlists are returned.
    assert playlists >= 10
    assert videos == 30


def test_get_video_items(session):
    videos = session.videos()
    mix = videos.categories[1].items[0]
    for item in mix.items():
        assert isinstance(item, tidalapi.Video)

    assert len(mix.items()) >= 25


def test_page_links(session):
    explore = session.explore()
    for item in explore.categories[2].items:
        page = item.get()
        if item.title == "TIDAL Rising":
            assert isinstance(page.categories[1].text, str)


def test_genres(session):
    genres = session.genres()
    first = next(iter(genres))
    assert first.title == "Blues"
    assert isinstance(next(iter(first.get())), tidalapi.Playlist)

    # NOTE local genres seems broken, and the first entry is no longer available
    local_genres = list(session.local_genres())
    first_local = local_genres[0]
    assert first_local != first
    assert isinstance(next(iter(local_genres[-1].get())), tidalapi.Playlist)


def test_moods(session):
    moods = session.moods()
    first = next(iter(moods))
    assert first.title == "For DJs"
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
