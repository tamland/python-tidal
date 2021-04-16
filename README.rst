tidalapi
========

.. image:: https://img.shields.io/pypi/v/tidalapi.svg
    :target: https://pypi.org/project/tidalapi

.. image:: https://api.netlify.com/api/v1/badges/f05c0752-4565-4940-90df-d2b3fe91c84b/deploy-status
    :target: https://0-6-x--tidalapi.netlify.app/

Unofficial Python API for TIDAL music streaming service.



0.7.0 Rewrite
-------------

Currently the project is being rewritten to make it easier to maintain and create documentation for, see https://github.com/tamland/python-tidal/projects/1 for progress. There may be breaking changes, but i might be able to keep the current usage for a deprecation period. Anyways, you should probably wait with writing pull requests until 0.7.0 has been released.

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
    tracks = session.get_album_tracks(album_id=16909093)
    for track in tracks:
        print(track.name)


Documentation
-------------

Documentation is available at https://0-6-x--tidalapi.netlify.app/
