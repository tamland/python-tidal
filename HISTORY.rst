.. :changelog:

History
-------

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
