=====
wimpy
=====

.. image:: https://badge.fury.io/py/wimpy.png
    :target: http://badge.fury.io/py/wimpy
    
.. image:: https://travis-ci.org/tamland/wimpy.png?branch=master
        :target: https://travis-ci.org/tamland/wimpy


Unofficial WiMP Python API


Example usage
-------------

.. code-block:: python

    from wimpy import Session

    wimp = Session()
    wimp.login('username', 'password')
    tracks = wimp.get_album_tracks(album_id=16909093)
    for track in tracks:
        print(track.name)


TODO
-----

- OO API (let's see how long until the web API changes first)
- Implement POST methods (edit playlists, add favourites etc.)
