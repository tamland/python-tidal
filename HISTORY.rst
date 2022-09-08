.. :changelog:

History
=======

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
