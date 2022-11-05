
Config
======

Here is an example of how you can modify the quality of tracks and videos, historically this has
been done before initializing the session, since some api keys didn't support all qualities.

.. testcode::

    import tidalapi

    config = tidalapi.Config(quality=tidalapi.Quality.lossless, video_quality=tidalapi.VideoQuality.low)
    session = tidalapi.Session(config)
