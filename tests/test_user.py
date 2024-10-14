# -*- coding: utf-8 -*-
#
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

import datetime

import dateutil.tz
import pytest

import tidalapi
from tidalapi.exceptions import ObjectNotFound


def test_user(session):
    assert isinstance(session.user, tidalapi.LoggedInUser)
    user = session.get_user(session.user.id)
    assert isinstance(user, tidalapi.LoggedInUser)
    assert "@" in user.email


def test_get_user(session):
    user = session.get_user(58600091)
    assert isinstance(user, tidalapi.FetchedUser)
    assert user.first_name == "Five Dragons"
    assert user.last_name == "Music"
    assert not user.picture_id


def test_get_user_playlists(session):
    user_playlists = session.user.playlists()
    user_favorite_playlists = session.user.favorites.playlists()
    user_playlists_and_favorite_playlists = []
    offset = 0
    while True:
        playlists = session.user.playlist_and_favorite_playlists(offset=offset)
        if playlists:
            user_playlists_and_favorite_playlists += playlists
        else:
            break
        offset += 50
    playlist_ids = set(x.id for x in user_playlists)
    favourite_ids = set(x.id for x in user_favorite_playlists)
    both_ids = set(x.id for x in user_playlists_and_favorite_playlists)

    assert playlist_ids | favourite_ids == both_ids


def test_get_playlist_folders(session):
    folder = session.user.create_folder(title="testfolder")
    assert folder
    folder_ids = [folder.id for folder in session.user.playlist_folders()]
    assert folder.id in folder_ids
    folder.remove()
    assert folder.id not in folder_ids


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
    playlist.add(["125169484"])
    assert playlist.tracks()[0].name == "Alone, Pt. II"
    assert playlist.description == "Testing1234"
    assert playlist.name == "Testing"
    playlist.remove_by_id("125169484")
    assert len(playlist.tracks()) == 0
    playlist.add(["64728757", "125169484"])
    for index, item in enumerate(playlist.tracks()):
        if item.name == "Alone, Pt. II":
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

    assert any(
        [playlist.id == user_playlist.id for user_playlist in session.user.playlists()]
    )
    assert any(
        [isinstance(user_playlist, tidalapi.UserPlaylist)]
        for user_playlist in session.user.playlists()
    )

    long_playlist = session.playlist("944dd087-f65c-4954-a9a3-042a574e86e3")
    playlist_tracks = long_playlist.tracks(limit=250)

    playlist.add([track.id for track in playlist_tracks])
    playlist._reparse()
    playlist.remove_by_id("199477058")
    playlist._reparse()

    track_ids = [track.id for track in playlist.tracks(limit=250)]
    assert 199477058 not in track_ids

    playlist.delete()


def test_create_folder(session):
    folder = session.user.create_folder(title="testfolder")
    assert folder.name == "testfolder"
    assert folder.parent is None
    assert folder.parent_folder_id == "root"
    assert folder.listen_url == f"https://listen.tidal.com/folder/{folder.id}"
    assert folder.total_number_of_items == 0
    assert folder.trn == f"trn:folder:{folder.id}"
    folder_id = folder.id

    # update name
    folder.rename(name="testfolder1")
    assert folder.name == "testfolder1"

    # cleanup
    folder.remove()

    # check if folder has been removed
    with pytest.raises(ObjectNotFound):
        session.folder(folder_id)


def test_folder_add_items(session):
    folder = session.user.create_folder(title="testfolder")
    folder_a = session.folder(folder.id)
    assert isinstance(folder_a, tidalapi.playlist.Folder)
    assert folder_a.id == folder.id

    # create a playlist and add it to the folder
    playlist_a = session.user.create_playlist("TestingA", "Testing1234")
    playlist_a.add(["125169484"])
    playlist_b = session.user.create_playlist("TestingB", "Testing1234")
    playlist_b.add(["125169484"])
    folder.add_items([playlist_a.id, playlist_b.id])

    # verify items
    assert folder.total_number_of_items == 2
    items = folder.items()
    assert len(items) == 2
    item_ids = [item.id for item in items]
    assert playlist_a.id in item_ids
    assert playlist_b.id in item_ids

    # cleanup (This will also delete playlists inside the folder!)
    folder.remove()


def test_folder_moves(session):
    folder_a = session.user.create_folder(title="testfolderA")
    folder_b = session.user.create_folder(title="testfolderB")

    # create a playlist and add it to the folder
    playlist_a = session.user.create_playlist("TestingA", "Testing1234")
    playlist_a.add(["125169484"])
    playlist_b = session.user.create_playlist("TestingB", "Testing1234")
    playlist_b.add(["125169484"])
    folder_a.add_items([playlist_a.id, playlist_b.id])

    # verify items
    assert folder_a.total_number_of_items == 2
    assert folder_b.total_number_of_items == 0
    items = folder_a.items()
    item_ids = [item.id for item in items]

    # move items to folder B
    folder_a.move_items_to_folder(trns=item_ids, folder=folder_b.id)
    folder_b._reparse()  # Manually refresh, as src folder contents will have changed
    assert folder_a.total_number_of_items == 0
    assert folder_b.total_number_of_items == 2
    item_a_ids = [item.id for item in folder_a.items()]
    item_b_ids = [item.id for item in folder_b.items()]
    assert playlist_a.id not in item_a_ids
    assert playlist_b.id not in item_a_ids
    assert playlist_a.id in item_b_ids
    assert playlist_b.id in item_b_ids

    # move items to the root folder
    folder_b.move_items_to_root(trns=item_ids)
    assert folder_a.total_number_of_items == 0
    assert folder_b.total_number_of_items == 0
    folder_b.move_items_to_folder(trns=item_ids)
    assert folder_b.total_number_of_items == 2

    # cleanup (This will also delete playlists inside the folders, if they are still there
    folder_a.remove()
    folder_b.remove()


def test_add_remove_folder(session):
    folder = session.user.create_folder(title="testfolderA")
    folder_id = folder.id
    # remove folder from favourites
    session.user.favorites.remove_folders_playlists([folder.id])
    # check if folder has been removed
    with pytest.raises(ObjectNotFound):
        session.folder(folder_id)


def test_add_remove_favorite_artist(session):
    favorites = session.user.favorites
    artist_id = 5247488
    add_remove(
        artist_id, favorites.add_artist, favorites.remove_artist, favorites.artists
    )


def test_add_remove_favorite_album(session):
    favorites = session.user.favorites
    album_id = 32961852
    add_remove(album_id, favorites.add_album, favorites.remove_album, favorites.albums)


def test_add_remove_favorite_playlist(session):
    favorites = session.user.favorites
    playlists_and_favorite_playlists = session.user.playlist_and_favorite_playlists
    playlist_id = "e676056d-fbc6-499a-be9d-7191d2d0bfee"
    add_remove(
        playlist_id,
        favorites.add_playlist,
        favorites.remove_playlist,
        favorites.playlists,
    )
    add_remove(
        playlist_id,
        favorites.add_playlist,
        favorites.remove_playlist,
        playlists_and_favorite_playlists,
    )


def test_add_remove_favorite_track(session):
    favorites = session.user.favorites
    track_id = 32961853
    add_remove(track_id, favorites.add_track, favorites.remove_track, favorites.tracks)


def test_add_remove_favorite_video(session):
    favorites = session.user.favorites
    video_id = 160850422
    add_remove(video_id, favorites.add_video, favorites.remove_video, favorites.videos)


def test_get_favorite_mixes(session):
    favorites = session.user.favorites
    mixes = favorites.mixes()
    assert len(mixes) > 0
    assert isinstance(mixes[0], tidalapi.MixV2)


def add_remove(object_id, add, remove, objects):
    """Add and remove an item from favorites. Skips the test if the item was already in
    your favorites.

    :param object_id: Identifier of the object
    :param add: Function to add object to favorites
    :param remove: Function to remove object from favorites
    :param objects: Function to list objects in favorites
    """
    # If the item is already favorited, we don't want to do anything with it,
    # as it would result in the date it was favorited changing. Avoiding it
    # also lets us make sure that we won't remove something from the favorites
    # if the tests are cancelled.
    exists = False
    for item in objects():
        if item.id == object_id:
            exists = True
            model = type(item).__name__
            name = item.name
    if exists:
        reason = (
            "%s '%s' is already favorited, skipping to avoid changing the date it was favorited"
            % (model, name)
        )
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
