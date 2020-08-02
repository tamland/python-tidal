tidalapi
========

.. image:: https://img.shields.io/pypi/v/tidalapi.svg
    :target: https://pypi.org/project/tidalapi

.. image:: https://api.netlify.com/api/v1/badges/f05c0752-4565-4940-90df-d2b3fe91c84b/deploy-status
    :target: https://tidalapi.netlify.com/

Unofficial Python API for TIDAL music streaming service.



0.7.0 Rewrite
-------------

This is an experimental branch for the 0.7.0 rewrite. It is mostly finished, but it is missing somme documentatiand a new explore endpoint containing moods, featured items, suggestions and so on.

Installation
------------

Install from `PyPI <https://pypi.python.org/pypi/tidalapi/>`_ using ``pip``:

.. code-block:: bash

    $ pip install tidalapi



Example usage
-------------

.. code-block:: python

    import tidalapi

    session = tidalapi.Session()
    session.login('username', 'password')
    album = session.album(16909093)
    tracks = album.tracks()
    for track in tracks:
        print(track.name)


Documentation
-------------

Documentation is available at https://tidalapi.netlify.com
