.. :changelog:

History
=======

v0.7.4
------
* Load/store OAuth/PKCE session to file - tehkillerbee_
* Add PKCE login for HiRes - exislow_, arnesongit_
* Include request response on error. Print as warning - tehkillerbee_
* Fix tests - tehkillerbee_
* Bugfixes (artist.get_similar) - tehkillerbee_
* Favourite mixes refactoring - jozefKruszynski_
* Add typings for Playlist, UserPlaylist, Pages - arusahni_
* Update favorites.tracks to accept order and orderDirection params - Jimmyscene_

v0.7.3
------
* Official support for HI_RES FLAC quality - tehkillerbee_
* Add helper functions to set audio/video quality for current session - tehkillerbee_
* Added missing WELCOME_MIX MixType - tehkillerbee_
* Various image bugfixes - tehkillerbee_
* Add "for_you" page - tehkillerbee_
* Various test, poetry bugfixes - 2e0byo_
* Add typings for Artists and Users - arusahni_
* Add media metadata - jozefKruszynski_
* Add option to limit track radio length - jozefKruszynski_
* Downgrade minimum required version of requests JoshMock_



v0.7.2
------
* (BREAKING!) Drop support for python3.8 and older
* Improved tests - 2e0byo_
* Add type to album object - jozefKruszynski_
* Add mix images and tests - jozefKruszynski_
* Add mypy and fix immediate typing errors - arusahni_
* New attribute to media.Track() class: 'full_name' - WilliamGuisan_
* Fix Track.stream() method - ssnailed_
* Fixed key error for gender when parsing user json - mkaufhol_
* Drop (almost) all user data we don't use. - 2e0byo_
* Add typing for media, genres, mixes, and albums - arusahni_
* Replace TypedDict and NamedTuple with dataclasses - arusahni_
* Fix circular Imports and Typing - PretzelVector_

v0.7.1
------
* Quick fix for "got key error 'picture'" error. - BlackLight_
* Bring back Radio support - bjesus_
* Added function for multiple deletions at once bloedboemmel_
* Use UTC instead of local time for expiry_time lutzbuerkle_

v0.7.0
------

* (BREAKING!) Removed obsolete parameter session_id from load_oauth_session - lutzbuerkle_
* (BREAKING!) Drop support for python2.7 - morguldir_
* (BREAKING!) Change the architecture of the library to allow for using more files, see the migration guide - morguldir_
* Add support for tidal pages (e.g. home, videos and explore in the web ui) - morguldir_
* Add support for parsing mixes and retrieving the media - morguldir_
* Get rid of the old genre and mood support, you can now find them in the pages instead - morguldir_
* Update almost all of the json parsing and classes to include more fields - morguldir_
* Add complete docstrings to many of the functions - morguldir_
* Tests now cover almost all of the code - morguldir_
* Pylint scores are now much higher - morguldir_
* Add option to retrieve master quality tracks (I can't test this, but I believe it works as of writing) - morguldir_
* Add a few documentation pages explaining the basics - morguldir_
* Add support for modifying playlists - morguldir_
* Add a parameter to always fetch the track album if it's not provided - divadsn_
* Add function to retrieve the year and date from either the release data or the stream start date - divadsn_
* Improve the performance of the internal get_items() function by using extend - BlackLight_
* Properly deal with the api returning non-json results - BlackLight_
* Add support for retrieving the reviews of an album - retired-guy_


v0.6.10
-------
* Update the client secret - 1nikolas_
* Use a track url endpoint compatible with the new secret - morguldir_

v0.6.9
------

* Update the client secret - morguldir_
* Fix token_refresh() not correctly including the client secret - morguldir_

v0.6.8
------

* Support OAuth login through login_oauth_simple() and login_oauth() - morguldir_
* Support loading an OAuth session through load_oauth_session() - morguldir_
* Include more info when a request fails - morguldir_

v0.6.7
------

* Fix wimp images not resolving - ktnrg45_
* Made the favorite playlists function also return created playlists - morguldir_

v0.6.6
------

* Update api token and slightly obfuscate it - morguldir_

v0.6.5
------

* Update api token - morguldir_

v0.6.4
------

* Add parameter to search() allowing for more results (up to 300) - morguldir_
* Fix get_track_url() not returning anything - morguldir_

v0.6.3
------

* Fix quality options using enum names instead of values - morguldir_
* Handle situations where tidal doesn't set the version tag - morguldir_

v0.6.2
------

* Update lossless token - morguldir_
* Always use the same api token - morguldir_
* Include additional info when logging fails - morguldir_
* Make user_id and country_code optional when using load_session() - morguldir_
* Add version tag for Track - Husky22_
* Switch to netlify for documentation - morguldir_

.. _morguldir: https://github.com/morguldir
.. _Husky22: https://github.com/Husky22
.. _ktnrg45: https://github.com/ktnrg45
.. _1nikolas: https://github.com/1nikolas
.. _divadsn: https://github.com/divadsn
.. _BlackLight: https://github.com/BlackLight
.. _lutzbuerkle: https://github.com/lutzbuerkle
.. _retired-guy: https://github.com/retired-guy
.. _bjesus: https://github.com/bjesus
.. _bloedboemmel: https://github.com/bloedboemmel
.. _2e0byo: https://github.com/2e0byo
.. _jozefKruszynski: https://github.com/jozefKruszynski
.. _arusahni: https://github.com/arusahni
.. _WilliamGuisan: https://github.com/WilliamGuisan
.. _ssnailed: https://github.com/ssnailed
.. _mkaufhol: https://github.com/mkaufhol
.. _PretzelVector: https://github.com/PretzelVector
.. _tehkillerbee: https://github.com/tehkillerbee
.. _JoshMock: https://github.com/JoshMock
.. _exislow: https://github.com/exislow
.. _arnesongit: https://github.com/arnesongit
.. _Jimmyscene: https://github.com/Jimmyscene



