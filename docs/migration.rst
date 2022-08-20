
Migration guides
================


Migrating from 0.6.x -> 0.7.x
-----------------------------

This update added a lot more docstrings to functions, added pagination to most functions,
and it uses methods a lot more over functions that take id's, for example ``session.get_album_tracks(108064429)``
is now ``session.album(108064429).tracks()`` instead

Additionally a few of the pages have been deprecated on TIDAL's side and aren't being updated anymore, this applies to genres
and moods mostly, so see :ref:`pages` for how to find these at their new homes, but note that you will probably need to search

Searching will be a bit more robust now, since you pass actual types,
instead of keywords matching the types. See :class:`~tidalapi.session.Session.search` for details

Also generally instead of things like ``session.get_track(track_id)``, you will now use session.track(track_id)