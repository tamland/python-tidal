tidalapi
========

.. image:: https://img.shields.io/pypi/v/tidalapi.svg
    :target: https://pypi.org/project/tidalapi

.. image:: https://readthedocs.org/projects/tidalapi/badge/?version=latest
    :target: https://tidalapi.readthedocs.io/en/latest/

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

Documentation is available at https://tidalapi.readthedocs.io/en/latest/
