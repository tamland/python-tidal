
Playlists
=========

This library allows you to create, modify and delete playlists, note that this is mostly about
the :class:`tidalapi.playlist.UserPlaylist` class, you can't modify other's playlists


Creating a playlist
-------------------

.. testsetup::

    import tests.conftest
    import requests
    session = tests.conftest.login(requests.Session())

.. testcode::

    playlist = session.user.create_playlist("Example playlist", "An example of a playlist")
    print(playlist.name)

.. testoutput::
    :hide:

    Example playlist

Adding to a playlist
--------------------

.. testcode::

    playlist.add([133937137, 71823815])
    [print(x.name) for x in playlist.tracks()]

.. testoutput::
    :hide:

    Worlds Collide
    Lost Forever

Removing from a playlist
------------------------

.. testcode::

    playlist.remove_by_index(0)
    playlist.remove_by_id(71823815)
    print(playlist.tracks())

.. testoutput::
    :hide:

    []

Deleting a playlist
-------------------

.. testcode::

    playlist.delete()