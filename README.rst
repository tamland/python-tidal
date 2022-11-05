tidalapi
========

.. image:: https://img.shields.io/pypi/v/tidalapi.svg
    :target: https://pypi.org/project/tidalapi

.. image:: https://api.netlify.com/api/v1/badges/f05c0752-4565-4940-90df-d2b3fe91c84b/deploy-status
    :target: https://tidalapi.netlify.com/

Unofficial Python API for TIDAL music streaming service.


0.7.0 Rewrite
-------------

The 0.7.0 rewrite is now complete, see the `migration guide <https://tidalapi.netlify.app/migration.html#migrating-from-0-6-x-0-7-x>`_ for dealing with it

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
    # Will run until you visit the printed url and link your account
    session.login_oauth_simple()
    album = session.album(66236918)
    tracks = album.tracks()
    for track in tracks:
        print(track.name)


Documentation
-------------

Documentation is available at https://tidalapi.netlify.app/
