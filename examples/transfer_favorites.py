# Copyright (C) 2023- The Tidalapi Developers
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
#
"""transfer_favorites.py: Use this script to transfer your Tidal favourites from Tidal user A to Tidal user B"""
import logging
from pathlib import Path
import csv
import time
import sys

import tidalapi

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

oauth_file1 = Path("tidal-session.json")
oauth_file2 = Path("tidal-session-B.json")


class TidalSession:
    def __init__(self):
        self._active_session = tidalapi.Session()

    def get_uid(self):
        return self._active_session.user.id

    def get_session(self):
        return self._active_session


class TidalTransfer:
    def __init__(self):
        self.session_src = TidalSession()
        self.session_dst = TidalSession()

    def export_csv(self, my_tracks, my_albums, my_artists, my_playlists):
        logger.info("Exporting user A favorites to csv...")
        # save to csv file
        with open("fav_tracks.csv", "w") as file:
            wr = csv.writer(file, quoting=csv.QUOTE_ALL)
            for track in my_tracks:
                wr.writerow(
                    [
                        track.id,
                        track.user_date_added,
                        track.artist.name,
                        track.album.name,
                    ]
                )
        with open("fav_albums.csv", "w") as file:
            wr = csv.writer(file, quoting=csv.QUOTE_ALL)
            for album in my_albums:
                wr.writerow(
                    [album.id, album.user_date_added, album.artist.name, album.name]
                )
        with open("fav_artists.csv", "w") as file:
            wr = csv.writer(file, quoting=csv.QUOTE_ALL)
            for artist in my_artists:
                wr.writerow([artist.id, artist.user_date_added, artist.name])
        with open("fav_playlists.csv", "w") as file:
            wr = csv.writer(file, quoting=csv.QUOTE_ALL)
            for playlist in my_playlists:
                wr.writerow(
                    [playlist.id, playlist.created, playlist.type, playlist.name]
                )

    def do_transfer(self):
        # do login for src and dst Tidal account
        session_src = self.session_src.get_session()
        session_dst = self.session_dst.get_session()
        logger.info("Login to user A (source)...")
        if not session_src.login_session_file(oauth_file1):
            logger.error("Login to Tidal user...FAILED!")
            exit(1)
        logger.info("Login to user B (destination)...")
        if not session_dst.login_session_file(oauth_file2):
            logger.error("Login to Tidal user...FAILED!")
            exit(1)

        # get current user favourites (source)
        my_tracks = session_src.user.favorites.tracks()
        my_albums = session_src.user.favorites.albums()
        my_artists = session_src.user.favorites.artists()
        my_playlists = session_src.user.playlist_and_favorite_playlists()
        # my_mixes = self._active_session.user.mixes()

        # export to csv
        self.export_csv(my_tracks, my_albums, my_artists, my_playlists)

        # add favourites to new user
        logger.info("Adding favourites to Tidal user B...")
        for idx, track in enumerate(my_tracks):
            logger.info("Adding track {}/{}".format(idx, len(my_tracks)))
            try:
                session_dst.user.favorites.add_track(track.id)
                time.sleep(0.1)
            except:
                logger.error("error while adding track {} {}".format(track.id, track.name))

        for idx, album in enumerate(my_albums):
            logger.info("Adding album {}/{}".format(idx, len(my_albums)))
            try:
                session_dst.user.favorites.add_album(album.id)
                time.sleep(0.1)
            except:
                logger.error("error while adding album {} {}".format(album.id, album.name))

        for idx, artist in enumerate(my_artists):
            logger.info("Adding artist {}/{}".format(idx, len(my_artists)))
            try:
                session_dst.user.favorites.add_artist(artist.id)
                time.sleep(0.1)
            except:
                logger.error("error while adding artist {} {}".format(artist.id, artist.name))

        for idx, playlist in enumerate(my_playlists):
            logger.info("Adding playlist {}/{}".format(idx, len(my_playlists)))
            try:
                session_dst.user.favorites.add_playlist(playlist.id)
                time.sleep(0.1)
            except:
                logger.error(
                    "error while adding playlist {} {}".format(
                        playlist.id, playlist.name
                    )
                )


if __name__ == "__main__":
    TidalTransfer().do_transfer()
