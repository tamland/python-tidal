# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 morguldir
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

# morguldir: TODO: user playlists

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

    long_playlist = session.playlist("944dd087-f65c-4954-a9a3-042a574e86e3")
    playlist_tracks = long_playlist.tracks(limit=250)

    playlist.add(playlist.id for playlist in playlist_tracks)
    playlist._reparse()
    playlist.remove_by_id(43490214)
    playlist._reparse()

    assert all(playlist.id != 43490214 for playlist in playlist.tracks(limit=250))

    playlist.delete()


def test_add_remove_favorite_artist(session):
    favorites = session.user.favorites
    artist_id = 6159368
    add_remove(artist_id, favorites.add_artist, favorites.remove_artist, favorites.artists)


def test_add_remove_favorite_album(session):
    favorites = session.user.favorites
    album_id = 100572762
    add_remove(album_id, favorites.add_album, favorites.remove_album, favorites.albums)


def test_add_remove_favorite_playlist(session):
    favorites = session.user.favorites
    playlist_id = "7eafb342-141a-4092-91eb-da0012da3a19"
    add_remove(playlist_id, favorites.add_playlist, favorites.remove_playlist, favorites.playlists)


def test_add_remove_favorite_track(session):
    favorites = session.user.favorites
    track_id = 17491028
    add_remove(track_id, favorites.add_track, favorites.remove_track, favorites.tracks)


def test_add_remove_favorite_video(session):
    favorites = session.user.favorites
    video_id = 125506698
    add_remove(video_id, favorites.add_video, favorites.remove_video, favorites.videos)


def add_remove(object_id, add, remove, objects):
    """
    Add and remove an item from favorites. Adds it back if it already was in your favorites.

    :param object_id: Identifier of the object
    :param add: Function to add object to favorites
    :param remove: Function to remove object from favorites
    :param objects: Function to list objects in favorites
    """
    exists = any(item.id == object_id for item in objects())
    add(object_id)
    assert any(item.id == object_id for item in objects())
    remove(object_id)
    assert any(item.id == object_id for item in objects()) is False
    if exists:
        add(object_id)
