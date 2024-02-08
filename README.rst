tidalapi
========

.. image:: https://img.shields.io/pypi/v/tidalapi.svg
    :target: https://pypi.org/project/tidalapi

.. image:: https://api.netlify.com/api/v1/badges/f05c0752-4565-4940-90df-d2b3fe91c84b/deploy-status
    :target: https://tidalapi.netlify.com/

Unofficial Python API for TIDAL music streaming service.

Requires Python 3.9 or higher.

Installation
------------

Install from `PyPI <https://pypi.python.org/pypi/tidalapi/>`_ using ``pip``:

.. code-block:: bash

    $ pip install tidalapi


GStreamer
------------

Playback of certain audio qualities
Certain streaming qualities require gstreamer bad-plugins, e.g.:
```
sudo apt-get install gstreamer1.0-plugins-bad
```
This is mandatory to be able to play m4a streams and for playback of mpegdash or hls streams. Otherwise, you will likely get an error:
```
WARNING  [MainThread] mopidy.audio.actor Could not find a application/x-hls decoder to handle media.
WARNING  [MainThread] mopidy.audio.gst GStreamer warning: No decoder available for type 'application/x-hls'.
ERROR    [MainThread] mopidy.audio.gst GStreamer error: Your GStreamer installation is missing a plug-in.
```


Usage
-------------

For examples on how to use the api, see the `examples <https://github.com/tamland/python-tidal/tree/master/examples>`_  directory.

Documentation
-------------

Documentation is available at https://tidalapi.netlify.app/

Development
-----------

This project uses poetry for dependency management and packaging. To install dependencies and setup the project for development, run:

.. code-block:: bash
    
        $ pip install pipx
        $ pipx install poetry
        $ poetry install --no-root
