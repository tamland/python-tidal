tidalapi
========

.. image:: https://img.shields.io/pypi/v/tidalapi.svg
    :target: https://pypi.org/project/tidalapi

.. image:: https://api.netlify.com/api/v1/badges/f05c0752-4565-4940-90df-d2b3fe91c84b/deploy-status
    :target: https://tidalapi.netlify.com/

Unofficial Python API for TIDAL music streaming service.


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
    tracks = session.get_album_tracks(album_id=16909093)
    for track in tracks:
        print(track.name)


Documentation
-------------

Documentation is available at https://tidalapi.netlify.com
