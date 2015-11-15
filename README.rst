tidalapi
========

.. image:: https://badge.fury.io/py/tidalapi.png
    :target: http://badge.fury.io/py/tidalapi


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

Documentation is available at http://pythonhosted.org/tidalapi/
