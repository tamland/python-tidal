# -*- coding: utf-8 -*-
#
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

import pytest
import datetime
import dateutil.tz
import tidalapi
from .cover import verify_image_cover


def test_user(session):
    assert isinstance(session.user, tidalapi.LoggedInUser)
    user = session.get_user(session.user.id)
    assert isinstance(user, tidalapi.LoggedInUser)
    assert '@' in user.email
    assert user.accepted_eula


def test_get_user(session):
    user = session.get_user(58600091)
    assert isinstance(user, tidalapi.FetchedUser)
    assert user.first_name == "Five Dragons"
    assert user.last_name == "Music"

    verify_image_cover(session, user, [100, 210, 600])


def test_get_user_playlists(session):
    user_playlists = session.user.playlists()
    user_favorite_playlists = session.user.favorites.playlists()
    user_playlists_and_favorite_playlists = session.user.playlist_and_favorite_playlists()
    for item in user_playlists + user_favorite_playlists:
        assert any(item.id == playlist.id for playlist in user_playlists_and_favorite_playlists)
    assert len(user_playlists + user_favorite_playlists) - 1 == len(user_playlists_and_favorite_playlists)


def test_get_user_playlist_creator(session):
    playlist = session.playlist("944dd087-f65c-4954-a9a3-042a574e86e3")
    creator = playlist.creator
    assert isinstance(creator, tidalapi.PlaylistCreator)
    assert creator.id == 169584258
    assert creator.name == "user"


def test_get_editorial_playlist_creator(session):
    playlist = session.playlist("aa3611ff-5b25-4bbe-8ce4-36c678c3438f")
    creator = playlist.creator
    assert isinstance(creator, tidalapi.PlaylistCreator)
    assert creator.id == 0
    assert creator.name == "TIDAL"


def test_create_playlist(session):
    playlist = session.user.create_playlist("Testing", "Testing1234")
    playlist.add([125169484])
    assert playlist.tracks()[0].name == 'Alone, Pt. II'
    assert playlist.description == "Testing1234"
    assert playlist.name == "Testing"
    playlist.remove_by_id(125169484)
    assert len(playlist.tracks()) == 0
    playlist.add([64728757, 125169484])
    for index, item in enumerate(playlist.tracks()):
        if item.name == 'Alone, Pt. II':
            playlist.remove_by_index(index)
            break

    assert playlist.items()[0].id == 64728757
    playlist.remove_by_index(0)
    assert len(playlist.tracks()) == 0

    playlist.edit()
    playlist._reparse()
    assert playlist.name == "Testing"
    assert playlist.description == "Testing1234"

    playlist.edit("testing", "testing1234")
    playlist._reparse()
    assert playlist.name == "testing"
    assert playlist.description == "testing1234"

    assert any([playlist.id == user_playlist.id for user_playlist in session.user.playlists()])
    assert any([isinstance(user_playlist, tidalapi.UserPlaylist)] for user_playlist in session.user.playlists())

    long_playlist = session.playlist("944dd087-f65c-4954-a9a3-042a574e86e3")
    playlist_tracks = long_playlist.tracks(limit=250)

    playlist.add(playlist.id for playlist in playlist_tracks)
    playlist._reparse()
    playlist.remove_by_id(199477058)
    playlist._reparse()

    assert all(playlist.id != 199477058 for playlist in playlist.tracks(limit=250))

    playlist.delete()


def test_add_remove_favorite_artist(session):
    favorites = session.user.favorites
    artist_id = 5247488
    add_remove(artist_id, favorites.add_artist, favorites.remove_artist, favorites.artists)


def test_add_remove_favorite_album(session):
    favorites = session.user.favorites
    album_id = 32961852
    add_remove(album_id, favorites.add_album, favorites.remove_album, favorites.albums)


def test_add_remove_favorite_playlist(session):
    favorites = session.user.favorites
    playlists_and_favorite_playlists = session.user.playlist_and_favorite_playlists
    playlist_id = "e676056d-fbc6-499a-be9d-7191d2d0bfee"
    add_remove(playlist_id, favorites.add_playlist, favorites.remove_playlist, favorites.playlists)
    add_remove(playlist_id, favorites.add_playlist, favorites.remove_playlist, playlists_and_favorite_playlists)


def test_add_remove_favorite_track(session):
    favorites = session.user.favorites
    track_id = 32961853
    add_remove(track_id, favorites.add_track, favorites.remove_track, favorites.tracks)


def test_add_remove_favorite_video(session):
    favorites = session.user.favorites
    video_id = 160850422
    add_remove(video_id, favorites.add_video, favorites.remove_video, favorites.videos)


def add_remove(object_id, add, remove, objects):
    """
    Add and remove an item from favorites. Skips the test if the item was already in your favorites.

    :param object_id: Identifier of the object
    :param add: Function to add object to favorites
    :param remove: Function to remove object from favorites
    :param objects: Function to list objects in favorites
    """
    # If the item is already favorited, we don't want to do anything with it, as it would result in the date it was
    # favorited changing. Avoiding it also lets us make sure that we won't remove something from the favorites if
    # the tests are cancelled.
    exists = False
    for item in objects():
        if item.id == object_id:
            exists = True
            model = type(item).__name__
            name = item.name
    if exists:
        reason = "%s '%s' is already favorited, skipping to avoid changing the date it was favorited" % (model, name)
        pytest.skip(reason)

    current_time = datetime.datetime.now(tz=dateutil.tz.tzutc())
    add(object_id)
    for item in objects():
        if item.id == object_id:
            exists = True
            # Checks that the item was added after the function was called. TIDAL seems to be 150ms ahead some times.
            timedelta = current_time - item.user_date_added
            assert timedelta < datetime.timedelta(microseconds=150000)
    assert exists

    remove(object_id)
    assert any(item.id == object_id for item in objects()) is False
