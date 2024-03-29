
Pages
=====

Here is an example of how you can use the tidalapi.page module

See :class:`tidalapi.page` for additional information about the available fields and functions

Home, Explore and Videos
-------------------------

.. testsetup::

    import tests.conftest
    import requests
    session = tests.conftest.login(requests.Session())

Goes through these pages and prints all of the categories and items

.. testcode::

    from tidalapi.page import PageItem, PageLink
    from tidalapi.mix import Mix

    home = session.home()
    home.categories.extend(session.explore().categories)
    home.categories.extend(session.videos().categories)

    for category in home.categories:
        print(category.title)

    for category in home.categories:
        print(category.title)
        items = []
        for item in category.items:
            if isinstance(item, PageItem):
                items.append("\t" + item.short_header)
                items.append("\t" + item.short_sub_header[0:50])
                # Call item.get() on this one, for example on click
            elif isinstance(item, PageLink):
                items.append("\t" + item.title)
                # Call item.get() on this one, for example on click
            elif isinstance(item, Mix):
                items.append("\t" + item.title)
                # You can optionally call item.get() to request the items() first, but it does it for you if you don't
            else:
                items.append("\t" + item.name)
                # An album could be handled by session.album(item.id) for example,
                # to get full details. Usually the relevant info is there already however
            print()
        [print(x) for x in sorted(items)]

.. testoutput::
    :hide:
    :options: +ELLIPSIS, +NORMALIZE_WHITESPACE

    For You...
    Recently Played...
    Suggested New Tracks...
    Suggested New Albums...
    Mixes For You...
    Radio Stations for You...
    Your History...
    Trending Playlists...
    Popular Playlists...
    TIDAL Rising...
    The Charts...
    Popular Albums...
    Podcasts...
    Radio Stations for You...
    Producers & Songwriters...
    New Releases For You...
    Featured...
    Genres...
    Moods, Activities & Events...

    Suggested Albums for You...
    Suggested Artists for You...
    Featured...
    Mixes For You...
    TIDAL Originals...
    New Music Videos...
    Album Experiences...
    New Video Playlists...
    Classics Video Playlists...
    Movies...
    Hits Video Playlists...
